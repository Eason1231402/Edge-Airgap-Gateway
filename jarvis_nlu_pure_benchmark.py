"""
Jarvis NLU 纯净基准测试脚本
------------------------------------------
测量目标：ask_jarvis_brain_edge() 函数本身的纯计算耗时
测量条件：单线程、无GPIO/MQTT/Flask/语音线程干扰、无磁盘IO

与 benchmark.py（全系统压力测试）的区别：
- benchmark.py 测量的是"完整系统在真实并发环境下"的端到端延迟，
  包含GIL线程调度开销、MQTT发布、日志记录等
- 本脚本测量的是"NLU意图解析算法本身"的理论下限延迟，
  对应论文中 Table/Fig 里引用的 0.002-0.056ms 量级数字

用法：python3 jarvis_nlu_pure_benchmark.py
"""

import time
import re
import csv
import statistics

# ==========================================
# === 颜色表（与 jarvis_main.py 保持一致） ===
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
# === 核心 NLU 解析函数（原样复制自 jarvis_main.py） ===
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
# === 基准测试主逻辑 ===
# ==========================================
TEST_COMMANDS = [
    "打开灯", "进入科技模式", "太亮了关灯", "我要复习数学了",
    "汇报系统状态", "变成血红色", "触发物理熔断", "恢复网络连接",
    "亮度调到50", "贾维斯进入安全模式"
]

WARMUP_ITERATIONS = 100      # 预热次数，不计入统计
BENCHMARK_ITERATIONS = 1000  # 正式测试次数


def run_pure_benchmark():
    print("=" * 60)
    print(" Jarvis NLU 纯净基准测试")
    print(f" 预热轮数: {WARMUP_ITERATIONS} | 正式轮数: {BENCHMARK_ITERATIONS}")
    print(" 测量条件: 单线程 / 无GPIO / 无MQTT / 无Flask / 无磁盘IO")
    print("=" * 60)

    # --- 预热阶段：让解释器完成缓存/分支预测热身 ---
    for _ in range(WARMUP_ITERATIONS):
        for cmd in TEST_COMMANDS:
            ask_jarvis_brain_edge(cmd)

    # --- 正式测试阶段 ---
    results = []
    for i in range(BENCHMARK_ITERATIONS):
        for cmd in TEST_COMMANDS:
            _, latency_sec = ask_jarvis_brain_edge(cmd)
            results.append({
                "Iteration": i + 1,
                "Command": cmd,
                "Latency_ms": latency_sec * 1000
            })

    # --- 导出CSV ---
    csv_filename = "jarvis_pure_nlu_benchmark_results.csv"
    with open(csv_filename, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["Iteration", "Command", "Latency_ms"])
        writer.writeheader()
        writer.writerows(results)

    # --- 按指令分组统计 ---
    print("\n--- 各指令延迟统计（毫秒） ---")
    print(f"{'指令':<15}{'均值':>10}{'最小值':>10}{'最大值':>10}{'标准差':>10}")
    for cmd in TEST_COMMANDS:
        latencies = [r["Latency_ms"] for r in results if r["Command"] == cmd]
        print(f"{cmd:<15}{statistics.mean(latencies):>10.5f}"
              f"{min(latencies):>10.5f}{max(latencies):>10.5f}"
              f"{statistics.stdev(latencies):>10.5f}")

    # --- 全局统计（对应论文引用数字） ---
    all_latencies = [r["Latency_ms"] for r in results]
    print("\n--- 全局统计摘要（用于论文引用） ---")
    print(f"总样本数:   {len(all_latencies)}")
    print(f"平均延迟:   {statistics.mean(all_latencies):.5f} ms")
    print(f"中位数:     {statistics.median(all_latencies):.5f} ms")
    print(f"最小值:     {min(all_latencies):.5f} ms")
    print(f"最大值:     {max(all_latencies):.5f} ms")
    print(f"标准差:     {statistics.stdev(all_latencies):.5f} ms")
    print(f"\n[SUCCESS] 原始数据已保存至 {csv_filename}")


if __name__ == "__main__":
    run_pure_benchmark()