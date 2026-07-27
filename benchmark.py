import time
import random
import csv
from jarvis_main import process_command, get_system_health, setup_gpio

# 模拟用户指令集
TEST_COMMANDS = [
    "打开灯", "进入科技模式", "太亮了关灯", "我要复习数学了", 
    "汇报系统状态", "变成血红色", "触发物理熔断", "恢复网络连接",
    "亮度调到50", "贾维斯进入安全模式"
]

def run_benchmark(iterations=50, delay=0.5):
    print(f"=== 启动硬件在环(HIL)自动化压力测试 ===")
    print(f"计划执行: {iterations} 次 | 间隔: {delay}s")
    print("警告: 继电器将频繁吸合，灯光将快速闪烁！\n")
    
    setup_gpio()
    results = []
    
    for i in range(iterations):
        cmd = random.choice(TEST_COMMANDS)
        
        # 记录执行前状态
        temp_before, mem_before = get_system_health()
        
        # 执行核心函数 (包含硬件动作)
        reply, latency = process_command(cmd)
        
        # 记录数据
        results.append({
            "Iteration": i + 1,
            "Command": cmd,
            "Latency_ms": round(latency, 4),
            "CPU_Temp_C": temp_before,
            "Mem_Usage_%": mem_before
        })
        
        print(f"[{i+1}/{iterations}] 指令: {cmd:<15} | 延迟: {latency:.3f}ms")
        time.sleep(delay)

    # 导出为 CSV 文件供论文作图使用
    csv_filename = "jarvis_benchmark_results.csv"
    with open(csv_filename, mode='w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=["Iteration", "Command", "Latency_ms", "CPU_Temp_C", "Mem_Usage_%"])
        writer.writeheader()
        writer.writerows(results)
        
    print(f"\n[SUCCESS] 测试完成！数据已保存至 {csv_filename}")
    
    # 打印统计摘要
    latencies = [r["Latency_ms"] for r in results]
    print(f"--- 论文数据摘要 ---")
    print(f"平均解析延迟: {sum(latencies)/len(latencies):.3f} ms")
    print(f"最大解析延迟: {max(latencies):.3f} ms")
    print(f"最小解析延迟: {min(latencies):.3f} ms")

if __name__ == "__main__":
    run_benchmark(iterations=50, delay=0.5)
