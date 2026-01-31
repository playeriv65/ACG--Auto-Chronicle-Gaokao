import sys
import os
sys.path.append(os.getcwd())

from novel_engine.core.simulator import SimulationEngine

def run():
    sim = SimulationEngine()
    print("正在初始化高维模拟引擎...")
    
    with open("outline_sim_v9.txt", "w", encoding="utf-8") as f:
        f.write("《拮抗中学：模拟人生版》\n")
        f.write("基于 v9.0 Simulation Engine\n")
        f.write("============================\n\n")
        
        grades = ["高一", "高二", "高三"]
        semesters = ["上", "下"]
        
        for g in grades:
            for s in semesters:
                f.write(f"=== {g}{s}学期 ===\n")
                sim.year = grades.index(g) + 1
                
                logs = sim.run_year()
                for log in logs:
                    f.write(f"[{log['week']}]\n")
                    for event in log['events']:
                        f.write(f"  - {event}\n")
                    f.write(f"  > 状态: {log['status']}\n")
                    f.write("\n")
                
                f.write("-" * 30 + "\n")

    print("模拟结束。请查看 outline_sim_v9.txt")

if __name__ == "__main__":
    run()

