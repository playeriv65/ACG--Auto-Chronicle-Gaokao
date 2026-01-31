import sys
import os
sys.path.append(os.getcwd())

from novel_engine.core.being_engine import BeingEngine

def run():
    print("正在构建第 10 版宇宙 (Classroom Simulation)...")
    engine = BeingEngine()
    
    with open("outline_v10_beings.txt", "w", encoding="utf-8") as f:
        f.write("《拮抗中学：众生相》\n")
        f.write("班级人数: 30 | 教师: 6 | 事件库: 100+\n")
        f.write("========================================\n\n")
        
        # 打印花名册
        f.write("【高一(3)班 花名册】\n")
        for i, s in enumerate(engine.students):
            f.write(f"{i+1}. {s.name} [{','.join(s.tags)}]\n")
        f.write("\n========================================\n\n")

        for w in range(1, 21):
            f.write(f"[第{w}周]\n")
            logs = engine.tick_week()
            for l in logs:
                f.write(f"  - {l}\n")
            
            # 每4周一次月考排名
            if w % 4 == 0:
                f.write(f"  --- 月考战报 ---\n")
                ranks = engine.get_rankings()
                top3 = ranks[:3]
                mc_rank = next(filter(lambda x: x[0]=="叶凌天", [(n,s) for n,s in ranks]))  # 修正元组解包逻辑
                # The ranks list contains tuples like ('Name', Score).
                # filter logic: x is ('Name', Score). x[0] is Name.
                # next returns the tuple ('叶凌天', Score).
                
                # Let's fix the logic to find MC rank index
                mc_idx = -1
                for idx, (n, s) in enumerate(ranks):
                    if n == "叶凌天":
                        mc_idx = idx + 1
                        break

                f.write(f"  前三甲: 1.{top3[0][0]}({top3[0][1]}) 2.{top3[1][0]}({top3[1][1]}) 3.{top3[2][0]}({top3[2][1]})\n")
                f.write(f"  主角排名: 第 {mc_idx} 名\n")
            
            f.write(f"  > {engine.get_mc_report()}\n\n")

    print("模拟完成。请查看 outline_v10_beings.txt")

if __name__ == "__main__":
    run()
