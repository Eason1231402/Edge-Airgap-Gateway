import pyaudio
p = pyaudio.PyAudio()
print("=== 系统音频输入设备列表 ===")
for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    if dev.get('maxInputChannels') > 0:
        print(f"Index {i}: {dev.get('name')}")
p.terminate()
