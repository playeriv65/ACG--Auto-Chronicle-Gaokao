import sys
import os
sys.path.append(os.getcwd())

from novel_engine.core.complex_fsm import DualFSM

OUTPUT_FILE = "script_outline_v8.txt"

def run_simulation():
    print("正在推演天机... (模拟三年高中生涯)")
    fsm = DualFSM()
    
    # Run until Graduated (Year 3 finished)
    while fsm.year <= 3:
        fsm.tick()
        if fsm.year == 3 and fsm.semester == 2 and fsm.week >= 19:
            break
            
    # Write to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("《拮抗中学：双修编年史》\n")
        f.write("生成引擎：v8.0 DualFSM\n")
        f.write("========================================\n\n")
        
        for entry in fsm.history_log:
            f.write(f"[{entry['date']}] 【{entry['state']}】\n")
            f.write(f"剧情：{entry['event']}\n")
            f.write(f"状态：{entry['stats']}\n")
            f.write("-" * 40 + "\n")
            
    print(f"推演完成！大纲已保存至：{OUTPUT_FILE}")
    print("请老板查阅大纲，确认剧情走向是否满意。")

if __name__ == "__main__":
    run_simulation()

