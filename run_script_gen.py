import sys
import os
import json
import sqlite3
import time
sys.path.append(os.getcwd())

from novel_engine.core.being_engine import BeingEngine
from novel_engine.core.ai_writer import writer

PLAN_FILE = "3_year_master_plan.txt"
QUIZ_DB = "novel_engine/data/quiz_bank.db"

def get_cached_quiz(week, subject, topic):
    conn = sqlite3.connect(QUIZ_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM quiz WHERE week=? AND subject=? AND topic=?", (week, subject, topic))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def save_to_cache(week, subject, topic, content):
    try:
        conn = sqlite3.connect(QUIZ_DB)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO quiz (week, subject, topic, content) VALUES (?, ?, ?, ?)", (week, subject, topic, content))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f" [DB Error] {e}")

def run_ultimate_simulation():
    print("正在开启‘大衍之术’（缓存增强版），推演三年天机...")
    engine = BeingEngine()
    engine.init_world()
    
    with open(PLAN_FILE, "w", encoding="utf-8") as f:
        f.write("《拮抗中学：三年因果全剧本 (Destiny Codex)》\n")
        f.write("="*60 + "\n\n")
        
        for year in [1]:
            engine.year = year
            for semester in [1]:
                engine.semester = semester
                f.write(f"\n<<< 高{year}{'上' if semester==1 else '下'}学期 >>>\n\n")
                
                for week in range(1, 21):
                    # 1. 引擎推演
                    logs, battle_type, quiz_raw = engine.tick(week)
                    abs_week = (year - 1) * 40 + (semester - 1) * 20 + week
                    
                    # 2. 题目处理 (查表 -> 调AI -> 存表)
                    quiz_final = None
                    if quiz_raw and isinstance(quiz_raw, dict) and quiz_raw.get("type") == "AI_GENERATED":
                        subject = quiz_raw['subject']
                        topic = quiz_raw['topic']
                        
                        # 查表
                        cached = get_cached_quiz(abs_week, subject, topic)
                        if cached:
                            quiz_final = cached
                        else:
                            # 调 AI
                            print(f" [Week {abs_week}] 命题组长闭关中，正在请求出题: {topic}...")
                            quiz_final = writer.generate_quiz(subject, topic)
                            # 存表
                            if quiz_final: save_to_cache(abs_week, subject, topic, quiz_final)
                    else:
                        quiz_final = quiz_raw

                    # 3. 记录
                    date_str = f"高{year}{'上' if semester==1 else '下'} 第{week:02d}周"
                    f.write(f"[{date_str}] 【{battle_type}】\n")
                    for l in logs: f.write(f"  {l}\n")
                    if quiz_final: f.write(f"\n【本周必杀真题】\n{quiz_final}\n")
                    
                    mc = engine.protagonist
                    rankings = engine.get_rankings()
                    f.write(f"  [因果记录] 状元:{rankings[0].name} | 主角:{engine.get_mc_report()}\n")
                    f.write("-" * 50 + "\n")
                    f.flush()

    print(f"\n[SUCCESS] 三年天命已定！剧本保存在: {PLAN_FILE}")

if __name__ == "__main__":
    run_ultimate_simulation()
