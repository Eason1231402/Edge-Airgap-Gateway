from flask import Flask, render_template, jsonify
import time

app = Flask(__name__)

# 这是一个模拟的全局状态字典。
# 未来我们会把它和你的 jarvis_main.py 里的真实变量打通！
system_state = {
    "wifi_relay": "ONLINE",  # 状态: ONLINE 或 SEVERED
    "light": "OFF",
    "curtain": "CLOSED",
    "logs": [
        {"time": time.strftime("%H:%M:%S"), "msg": "系统初始化完成..."},
        {"time": time.strftime("%H:%M:%S"), "msg": "Vosk 边缘语音引擎已加载至内存"},
        {"time": time.strftime("%H:%M:%S"), "msg": "等待语音指令接入..."}
    ]
}

@app.route('/')
def index():
    # 渲染刚才写的 HTML 页面
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    # 前端 JS 会每秒调用这个接口，获取最新状态
    return jsonify(system_state)

if __name__ == '__main__':
    print("===================================================")
    print("[J.A.R.V.I.S] Web 仪表盘服务已启动！")
    print("请在你的 Mac 浏览器中访问: http://192.168.1.105:5000")
    print("===================================================")
    # host='0.0.0.0' 允许局域网内其他设备（你的 Mac）访问
    app.run(host='0.0.0.0', port=5000, debug=True)
