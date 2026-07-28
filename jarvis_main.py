import RPi.GPIO as GPIO
import time
import paho.mqtt.client as mqtt
import json
import psutil
import threading
import os
import re
from flask import Flask, render_template, jsonify, request

# ==========================================
# === 核心配置参数 ===
# ==========================================
ENABLE_VOICE = True

RELAY_PIN = 17
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
ZIGBEE_DEVICE_ID = "0xXXXXXXXXXXXXXXXX"  # placeholder — replace with your own Zigbee device ID
MQTT_TOPIC_SET = f"zigbee2mqtt/{ZIGBEE_DEVICE_ID}/set"
MODEL_PATH = "models/vosk-model-cn"

# ==========================================
# === 全局状态字典 ===
# ==========================================
system_state = {
    "wifi_relay": "ONLINE",
    "light": "OFF",
    "light_brightness": 100,
    "light_color": "白色",
    "light_mode": "普通",
    "curtain": "CLOSED",
    "logs": []
}

# ==========================================
# === 日志模块 ===
# ==========================================
def add_log(msg):
    t = time.strftime("%H:%M:%S")
    system_state["logs"].append({"time": t, "msg": msg})
    if len(system_state["logs"]) > 20:
        system_state["logs"].pop(0)

# ==========================================
# === Flask Web 服务 ===
# ==========================================
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    return jsonify(system_state)

@app.route('/api/popup_data')
def popup_data():
    temp, mem = get_system_health()
    return jsonify({
        "light":            system_state["light"],
        "light_brightness": system_state["light_brightness"],
        "light_color":      system_state["light_color"],
        "light_mode":       system_state["light_mode"],
        "wifi_relay":       system_state["wifi_relay"],
        "curtain":          system_state["curtain"],
        "cpu_temp":         round(temp, 1),
        "mem_usage":        round(mem, 1),
        "log_latest":       system_state["logs"][-1]["msg"] if system_state["logs"] else ""
    })

@app.route('/api/command', methods=['POST'])
def web_command():
    data = request.get_json()
    cmd = data.get("cmd", "")
    if cmd:
        reply, latency = process_command(cmd, source="WEB")
        return jsonify({"reply": reply, "latency": round(latency * 1000, 3)})
    return jsonify({"reply": "无效指令", "latency": 0})

def run_web_server():
    import logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# ==========================================
# === MQTT 硬件控制层 (含异步防堵塞) ===
# ==========================================
try:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
except AttributeError:
    client = mqtt.Client()

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    add_log("[系统] Zigbee/MQTT 局域网链路已就绪")
except ConnectionRefusedError:
    print("\n[WARNING] MQTT 未启动，灯控暂不可用")
    add_log("[警告] MQTT 链路断开")

_last_mqtt_time = 0
_last_mqtt_payload = ""
_mqtt_timer = None  # 异步定时器，防止堵塞主线程

def _do_publish(payload_str):
    """真正执行 MQTT 发布的底层函数"""
    global _last_mqtt_time, _last_mqtt_payload
    client.publish(MQTT_TOPIC_SET, payload_str)
    _last_mqtt_time = time.time()
    _last_mqtt_payload = payload_str

def control_light(state="ON", brightness=None, color_temp=None,
                  color=None, clear_color=False, transition=0):
    global _last_mqtt_time, _last_mqtt_payload, _mqtt_timer
    
    payload = {"state": state, "transition": transition}

    if brightness is not None:
        payload["brightness"] = max(1, min(254, int(brightness)))
        system_state["light_brightness"] = round(brightness / 254 * 100)

    if color is not None:
        payload["color"] = color
    elif color_temp is not None:
        payload["color_temp"] = max(150, min(500, int(color_temp)))
        payload["color_mode"] = "color_temp"
    elif clear_color:
        payload["color_temp"] = 250
        payload["color_mode"] = "color_temp"

    payload_str = json.dumps(payload)
    
    # 1. 过滤短时间内完全重复的指令
    if payload_str == _last_mqtt_payload and (time.time() - _last_mqtt_time) < 2.0:
        return

    # 2. 异步非阻塞节流 (Throttle & Debounce)
    if _mqtt_timer is not None:
        _mqtt_timer.cancel()  # 取消旧指令，只发最新指令

    now = time.time()
    if (now - _last_mqtt_time) >= 0.4:
        _do_publish(payload_str)
    else:
        delay = 0.4 - (now - _last_mqtt_time)
        _mqtt_timer = threading.Timer(delay, _do_publish, args=[payload_str])
        _mqtt_timer.start()

    if state == "OFF":
        system_state["light"] = "OFF"
        add_log("[执行终端] 智能灯已关闭")
    else:
        system_state["light"] = "ON"
        add_log(f"[执行终端] 灯光指令已下发 → {payload}")

def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(RELAY_PIN, GPIO.OUT, initial=GPIO.HIGH)

def toggle_wifi_power(state):
    if state == "OFF":
        GPIO.output(RELAY_PIN, GPIO.LOW)
        system_state["wifi_relay"] = "SEVERED"
        add_log("[物理熔断] 广域网模块已强制断电 → 绝对隐私模式")
    else:
        GPIO.output(RELAY_PIN, GPIO.HIGH)
        system_state["wifi_relay"] = "ONLINE"
        add_log("[物理熔断] 广域网模块供电已恢复")

def get_system_health():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = float(f.read()) / 1000.0
    except:
        temp = 0.0
    mem = psutil.virtual_memory()
    return temp, mem.percent

# ==========================================
# === 颜色表 ===
# ==========================================
COLOR_MAP = {
    "红色": {"r": 255, "g": 0,   "b": 0},
    "红灯": {"r": 255, "g": 0,   "b": 0},
    "绿色": {"r": 0,   "g": 200, "b": 0},
    "绿灯": {"r": 0,   "g": 200, "b": 0},
    "蓝色": {"r": 0,   "g": 80,  "b": 255},
    "蓝灯": {"r": 0,   "g": 80,  "b": 255},
    "紫色": {"r": 160, "g": 0,   "b": 200},
    "紫灯": {"r": 160, "g": 0,   "b": 200},
    "粉色": {"r": 255, "g": 80,  "b": 160},
    "橙色": {"r": 255, "g": 80,  "b": 0},
    "黄色": {"r": 255, "g": 180, "b": 0},
    "青色": {"r": 0,   "g": 220, "b": 220},
    "白色": {"r": 255, "g": 255, "b": 255},
    "暖白": {"r": 255, "g": 200, "b": 120},
}

# ==========================================
# === 边缘计算大脑：扁平优先级NLU ===
# ==========================================
def ask_jarvis_brain_edge(text):
    start_time = time.perf_counter()
    action = "none"
    reply  = "指令已记录。"
    params = {}

    for color_name, rgb in COLOR_MAP.items():
        if color_name in text:
            action = "color_rgb"
            params["color"] = rgb
            params["color_name"] = color_name
            reply = f"已切换为{color_name}。"
            break

    if action == "none":
        if any(w in text for w in ["科幻", "黑客", "赛博朋克", "科技"]):
            action = "scene_tech"
            reply = "科技模式已激活。"
        elif any(w in text for w in ["浪漫", "约会"]):
            action = "scene_romance"
            reply = "浪漫氛围已就绪。"
        elif any(w in text for w in ["电影", "影院", "看片"]):
            action = "scene_movie"
            reply = "影院模式已启动。"
        elif any(w in text for w in ["起床", "早安", "唤醒"]):
            action = "scene_morning"
            reply = "唤醒照明已开启。"
        elif any(w in text for w in ["考研", "备考", "专注", "学习"]):
            action = "scene_study"
            reply = "专注模式已启动。"

    if action == "none":
        if any(w in text for w in ["暖光", "暖色", "橙光", "黄光", "睡前", "睡觉"]):
            action = "color_temp"
            params["color_temp"] = 450
            reply = "已切换至暖黄光。"
        elif any(w in text for w in ["冷光", "冷白", "日光", "看书", "阅读"]):
            action = "color_temp"
            params["color_temp"] = 150
            reply = "已切换至冷白光。"
        elif any(w in text for w in ["自然光", "中性光", "标准色温"]):
            action = "color_temp"
            params["color_temp"] = 300
            reply = "已切换至自然白光。"
        else:
            m = re.search(r'色温.*?(\d+)', text)
            if m:
                action = "color_temp"
                params["color_temp"] = int(m.group(1))
                reply = f"色温已调整至 {m.group(1)}。"

    if action == "none":
        if any(w in text for w in ["最亮", "全亮", "亮度最大"]):
            action = "brightness"
            params["brightness"] = 254
            reply = "亮度已调至最大。"
        elif any(w in text for w in ["最暗", "亮度最小", "调最暗"]):
            action = "brightness"
            params["brightness"] = 10
            reply = "亮度已调至最低。"
        elif any(w in text for w in ["调暗", "暗一点", "暗些", "降低亮度", "亮度低"]):
            action = "brightness_down"
            reply = "亮度已降低。"
        elif any(w in text for w in ["调亮", "亮一点", "亮些", "提高亮度", "亮度高"]):
            action = "brightness_up"
            reply = "亮度已提升。"
        else:
            m = re.search(r'亮度.*?(\d+)', text)
            if not m:
                m = re.search(r'(\d+).*?亮度', text)
            if m:
                val = int(m.group(1))
                if val <= 100:
                    val = int(val / 100 * 254)
                action = "brightness"
                params["brightness"] = val
                reply = f"亮度已调整至 {round(val/254*100)}%。"

    if action == "none":
        if any(w in text for w in ["开灯", "打开灯", "亮灯", "开一下灯", "把灯打开"]):
            action = "light_on"
            reply = "照明已开启。"
        elif any(w in text for w in ["关灯", "关闭灯", "熄灯", "灭灯", "把灯关"]):
            action = "light_off"
            reply = "照明已关闭。"

    if action == "none":
        if any(w in text for w in ["熔断", "隐私模式", "断网", "安全模式", "防窃听", "物理断网"]):
            action = "net_cut"
            reply = "物理熔断已触发，纯局域网安全模式。"
        elif any(w in text for w in ["恢复网络", "取消熔断", "联网", "解除安全", "恢复联网"]):
            action = "net_restore"
            reply = "物理熔断已解除，供电已恢复。"

    if action == "none":
        if any(w in text for w in ["自检", "状态", "汇报", "系统信息", "温度"]):
            action = "sys_status"
            reply = "正在执行边缘计算核心自检..."

    latency = time.perf_counter() - start_time
    return {"action": action, "reply": reply, "params": params}, latency

# ==========================================
# === 行为中枢 ===
# ==========================================
_current_brightness = 200

def process_command(cmd, source="USER"):
    global _current_brightness

    add_log(f"[{source}] {cmd}")
    intent_data, latency = ask_jarvis_brain_edge(cmd)
    action = intent_data["action"]
    reply  = intent_data["reply"]
    params = intent_data["params"]

    if action == "light_on":
        control_light("ON", brightness=_current_brightness, clear_color=True)
        system_state["light_mode"] = "普通"
        system_state["light_color"] = "白色"

    elif action == "light_off":
        control_light("OFF")

    elif action == "brightness":
        bv = params.get("brightness", 200)
        _current_brightness = bv
        control_light("ON", brightness=bv, clear_color=True)

    elif action == "brightness_up":
        _current_brightness = min(254, _current_brightness + 50)
        control_light("ON", brightness=_current_brightness)
        reply = f"亮度已提升至 {round(_current_brightness/254*100)}%。"

    elif action == "brightness_down":
        _current_brightness = max(10, _current_brightness - 50)
        control_light("ON", brightness=_current_brightness)
        reply = f"亮度已降低至 {round(_current_brightness/254*100)}%。"

    elif action == "color_temp":
        ct = params.get("color_temp", 300)
        control_light("ON", brightness=_current_brightness, color_temp=ct)
        system_state["light_color"] = "色温模式"

    elif action == "color_rgb":
        rgb  = params.get("color", {"r": 255, "g": 255, "b": 255})
        name = params.get("color_name", "自定义")
        control_light("ON", brightness=_current_brightness, color=rgb)
        system_state["light_color"] = name
        system_state["light_mode"]  = f"{name}模式"

    elif action == "scene_tech":
        _current_brightness = 200
        control_light("ON", brightness=200, color={"r": 0, "g": 200, "b": 255})
        system_state["light_mode"] = "科技"
        system_state["light_color"] = "青蓝"

    elif action == "scene_romance":
        _current_brightness = 80
        control_light("ON", brightness=80, color={"r": 180, "g": 80, "b": 220})
        system_state["light_mode"] = "浪漫"
        system_state["light_color"] = "玫粉"

    elif action == "scene_movie":
        _current_brightness = 60
        control_light("ON", brightness=60, color_temp=400)
        system_state["light_mode"] = "电影"

    elif action == "scene_morning":
        _current_brightness = 180
        control_light("ON", brightness=180, color_temp=200)
        system_state["light_mode"] = "唤醒"

    elif action == "scene_study":
        _current_brightness = 254
        control_light("ON", brightness=254, color_temp=150)
        system_state["light_mode"] = "考研专注"
        system_state["light_color"] = "冷白"

    elif action == "net_cut":
        toggle_wifi_power("OFF")
        control_light("ON", brightness=150, color={"r": 255, "g": 0, "b": 0})
        system_state["light_mode"]  = "熔断警示"
        system_state["light_color"] = "红色"

    elif action == "net_restore":
        toggle_wifi_power("ON")
        control_light("ON", brightness=_current_brightness, clear_color=True)
        system_state["light_mode"]  = "普通"
        system_state["light_color"] = "白色"

    elif action == "sys_status":
        temp, mem = get_system_health()
        reply = (f"边缘计算核心正常。CPU {temp:.1f} 度，"
                 f"内存占用 {mem:.0f}%，"
                 f"广域网状态 {system_state['wifi_relay']}。")

    final_reply = f"[JARVIS] {reply}"
    print(f"[NLU 解析耗时] {latency*1000:.3f} ms ✓")
    add_log(f"[JARVIS] {reply[:50]}")

    return final_reply, latency

# ==========================================
# === 听觉神经：离线语音监听 (含硬件防锁死) ===
# ==========================================
def voice_listener_thread():
    if not ENABLE_VOICE:
        return
    try:
        import pyaudio
        from vosk import Model, KaldiRecognizer
    except ImportError:
        print("[ERROR] 缺少 pyaudio 或 vosk 库")
        return

    if not os.path.exists(MODEL_PATH):
        print(f"\n[ERROR] 找不到 Vosk 模型: {MODEL_PATH}")
        return

    print("\n[SYSTEM] 正在加载 Kaldi/Vosk 离线声学模型...")
    model = Model(MODEL_PATH)
    
    grammar_list = [
        "贾维斯", 
        "开灯", "关灯", "打开灯", "关闭灯",
        "红色", "绿色", "蓝色", "黄色", "青色", "白色", "紫色", "粉色", "橙色",
        "科幻模式", "科技模式", "浪漫模式", "专注模式", "考研模式", "影院模式",
        "调高亮度", "调低亮度", "亮度最大", "亮度最小", "最亮", "最暗", "调亮", "调暗",
        "暖光", "冷光", "自然光", "冷白", "暖白",
        "进入隐私模式", "物理熔断", "物理断网", "恢复网络", "取消熔断",
        "自检", "状态",
        "[unk]"
    ]
    grammar = json.dumps(grammar_list, ensure_ascii=False)
    rec = KaldiRecognizer(model, 16000, grammar)

    p = pyaudio.PyAudio()
    stream = None
    
    print("\n[AUDIO] 正在连接麦克风...")
    
    # 🚀 核心修复：军工级音频接管逻辑，防 ALSA 死锁
    try:
        # 尝试 1：直接连接默认通道
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000,
                        input=True, frames_per_buffer=4000)
    except Exception as e:
        print(f"\n[WARNING] 默认通道异常 ({e})，启动硬件级扫描...")
        # 尝试 2：遍历所有硬件，寻找可用的重采样通道
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if dev.get('maxInputChannels', 0) > 0:
                try:
                    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000,
                                    input=True, frames_per_buffer=4000, input_device_index=i)
                    print(f"[SUCCESS] 已强制接管音频设备: {dev.get('name')}")
                    break
                except Exception:
                    continue

    if stream is None:
        print("\n[FATAL] 麦克风硬件被 Linux 底层死锁！")
        print("👉 解决方案：请在终端执行 killall python 或 sudo reboot 重启树莓派。")
        return

    stream.start_stream()
    print("[SUCCESS] USB 麦克风已激活，底层重采样通道已建立，离线监听中...")
    add_log("[系统] 离线语音引擎已激活")

    while True:
        try:
            data = stream.read(4000, exception_on_overflow=False)
        except Exception:
            continue
            
        partial_res = json.loads(rec.PartialResult())
        partial_text = partial_res.get("partial", "").replace(" ", "")
        
        if len(partial_text) >= 2:
            intent, _ = ask_jarvis_brain_edge(partial_text)
            if intent["action"] != "none":
                print(f"\n[VOICE 闪电截获] {partial_text}")
                reply, _ = process_command(partial_text, source="VOICE-FAST")
                print(f"{reply}\n[USER] 请输入自然语言: ", end="", flush=True)
                rec.Reset()
                continue

        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text   = result.get("text", "").replace(" ", "")
            if text:
                print(f"\n[VOICE FULL] {text}")
                reply, _ = process_command(text, source="VOICE")
                print(f"{reply}\n[USER] 请输入自然语言: ", end="", flush=True)

# ==========================================
# === 主循环 ===
# ==========================================
def main():
    setup_gpio()

    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    voice_thread = threading.Thread(target=voice_listener_thread, daemon=True)
    voice_thread.start()

    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "127.0.0.1"

    print("=" * 60)
    print(" J.A.R.V.I.S 边缘计算核心 v8.0 [静默暗影版]")
    print("=" * 60)
    print(f" [Web 主控界面] 请在 Mac 浏览器中打开:")
    print(f" 🌐 http://{local_ip}:5000")
    print("=" * 60)

    try:
        while True:
            cmd = input("\n[USER] 请输入自然语言: ")
            if not cmd:
                continue
            if cmd in ["退出", "exit", "quit"]:
                break
            reply, _ = process_command(cmd, source="TEXT")
            print(reply)

    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
        client.loop_stop()
        client.disconnect()
        print("\n[SYSTEM] 核心系统已安全下线。")

if __name__ == "__main__":
    main()
