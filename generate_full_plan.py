import sys
import os
import json
import time
sys.path.append(os.getcwd())

import sqlite3
from novel_engine.core.being_engine import BeingEngine
from novel_engine.core.ai_writer import writer

PLAN_FILE = "3_year_master_plan.txt"
QUIZ_DB = "novel_engine/data/storage/course_data.db"

def get_cached_quiz(week, subject, topic):
    if not os.path.exists(QUIZ_DB): return None
    try:
        conn = sqlite3.connect(QUIZ_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM quiz WHERE week=? AND subject=? AND topic=?", (week, subject, topic))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    except: return None

def save_to_cache(week, subject, topic, content):
    try:
        conn = sqlite3.connect(QUIZ_DB)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS quiz (id INTEGER PRIMARY KEY AUTOINCREMENT, week INTEGER, subject TEXT, topic TEXT, content TEXT, UNIQUE(week, subject, topic))")
        cursor.execute("INSERT OR REPLACE INTO quiz (week, subject, topic, content) VALUES (?, ?, ?, ?)", (week, subject, topic, content))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f" [DB Error] {e}")

def run_plan():
    print("正在开启‘造化鼎’（缓存增强版），推演拮抗中学三年因果...")
    engine = BeingEngine()
    engine.init_world()
    
    with open(PLAN_FILE, "w", encoding="utf-8") as f:
        f.write("《拮抗中学：三年因果全剧本 (Ultimate Edition)》\n")
        f.write(f"推演时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60 + "\n\n")
        
        # 1. 记录全班灵魂设定 (确保持久化一致性)
        f.write("【第一卷：众生法相】\n")
        for s in engine.students:
            f.write(f"- {s.name}({s.gender}) | {s.get_soul_desc()} | 属性:{s.tags}\n")
        f.write("\n" + "="*60 + "\n\n")

        # 2. 推演 120 周
        f.write("【第二卷：三年征途】\n")
        for year in [1, 2, 3]:
            engine.year = year
            for semester in [1, 2]:
                engine.semester = semester
                f.write(f"\n--- 高{year}{'上' if semester==1 else '下'}学期 ---\n")
                print(f" -> 正在推演: 高{year}{'上' if semester==1 else '下'}...")
                
                for week in range(1, 21):
                    # 推演一周数值
                    logs, battle_type, quiz_raw = engine.tick(week)
                    abs_week = (year - 1) * 40 + (semester - 1) * 20 + week
                    
                    # 实时命题 (如果是周考)
                    quiz_final = quiz_raw
                    if quiz_raw and isinstance(quiz_raw, dict) and quiz_raw.get("type") == "AI_GENERATED":
                        subject = quiz_raw['subject']
                        topic = quiz_raw['topic']
                        
                        # 1. 查缓存
                        cached = get_cached_quiz(abs_week, subject, topic)
                        if cached:
                            quiz_final = cached
                        else:
                            # 2. 调 AI
                            print(f"    [Week {week:02d}] 正在请‘判官’命题: {topic}...")
                            quiz_final = writer.generate_quiz(subject, topic)
                            # 3. 存缓存
                            if quiz_final: save_to_cache(abs_week, subject, topic, quiz_final)
                    
                    # 记录剧本
                    date_str = f"G{year}S{semester}_W{week:02d}"
                    f.write(f"[{date_str}] 【{battle_type}】\n")
                    for l in logs: f.write(f"  {l}\n")
                    
                    if quiz_final:
                        f.write(f"  [本周真题]\n  {str(quiz_final).replace(chr(10), chr(10)+'  ')}\n")
                    
                    # 记录当时排名
                    mc = engine.protagonist
                    rankings = engine.get_rankings()
                    f.write(f"  [因果记录] 主角排名:{engine.get_mc_report()} | 榜首:{rankings[0].name}\n")
                    f.write("-" * 40 + "\n")
                    f.flush() # 实时落盘

    print(f"\n[SUCCESS] 三年天命已定！剧本保存在: {PLAN_FILE}")

if __name__ == "__main__":
    run_plan()
