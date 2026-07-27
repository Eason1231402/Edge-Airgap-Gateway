import os
import json
from vosk import Model, KaldiRecognizer

# 模型路径
MODEL_PATH = "models/vosk-model-cn"

def init_voice_engine():
    """
    初始化 Vosk 离线语音识别引擎
    对应专利 T2 步骤：调用轻量化 Vosk 离线引擎
    """
    print("[SYSTEM] 正在将 Vosk 离线声学模型加载至内存...")
    
    if not os.path.exists(MODEL_PATH):
        print(f"[ERROR] 致命错误：未找到本地模型文件 {MODEL_PATH}")
        print("请确保已下载模型并放置在正确路径。")
        return None
    
    try:
        # 加载模型 (这一步会把模型读入内存，可能需要一两秒)
        model = Model(MODEL_PATH)
        # 初始化识别器，设定采样率为 16000 Hz (麦克风标准采样率)
        recognizer = KaldiRecognizer(model, 16000)
        print("[SUCCESS] Vosk 离线语音引擎初始化完成！(完全物理隔离)")
        return recognizer
    except Exception as e:
        print(f"[ERROR] 模型加载失败: {e}")
        return None

if __name__ == "__main__":
    # 单元测试：仅测试模型是否能成功加载进内存
    print("=== 启动离线语音引擎自检 ===")
    rec = init_voice_engine()
    
    if rec:
        print("\n[STATUS] 引擎已就绪。")
        print("[INFO] 等待麦克风阵列硬件接入后，即可开启实时监听流...")
