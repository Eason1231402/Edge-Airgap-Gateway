import paho.mqtt.client as mqtt
import json
import time

# 配置参数
BROKER = "127.0.0.1"  # 本地 MQTT 服务器
PORT = 1883
ZIGBEE_DEVICE_ID = "0xXXXXXXXXXXXXXXXX"  # placeholder — replace with your own Zigbee device ID
TOPIC_SET = f"zigbee2mqtt/{ZIGBEE_DEVICE_ID}/set"

# 初始化 MQTT 客户端
client = mqtt.Client()

def connect_mqtt():
    try:
        client.connect(BROKER, PORT, 60)
        client.loop_start()
        print("[INFO] Jarvis 神经中枢 (MQTT) 连接成功。")
    except Exception as e:
        print(f"[ERROR] 连接失败: {e}")

def control_light(state, brightness=None, color_temp=None, color=None):
    """
    发送控制指令给灯泡
    """
    payload = {"state": state}
    if brightness is not None:
        payload["brightness"] = brightness
    if color_temp is not None:
        payload["color_temp"] = color_temp
    if color is not None:
        payload["color"] = color
        
    # 将字典转换为 JSON 字符串并发送
    client.publish(TOPIC_SET, json.dumps(payload))
    print(f"[CMD] 发送指令 -> {payload}")

if __name__ == "__main__":
    connect_mqtt()
    time.sleep(1) # 等待连接建立

    print("\n[SYSTEM] 开始执行环境光初始化序列...")
    
    try:
        # 1. 开启并设置为科技蓝 (Jarvis 经典色)
        control_light("ON", brightness=200, color={"x": 0.15, "y": 0.15})
        time.sleep(2)
        
        # 2. 亮度调暗，营造思考氛围
        control_light("ON", brightness=50)
        time.sleep(2)
        
        # 3. 切换为适合学习/工作的暖白光
        control_light("ON", brightness=254, color_temp=250)
        print("\n[SYSTEM] 初始化完成，工作环境已就绪。")
        
    except KeyboardInterrupt:
        print("\n[INFO] 终止序列。")
    finally:
        client.loop_stop()
        client.disconnect()
