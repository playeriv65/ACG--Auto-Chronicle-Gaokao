import sys
import os
import json
import time
import argparse
import sqlite3
sys.path.append(os.getcwd())

from novel_engine.core.being_engine import BeingEngine
from novel_engine.core.ai_writer import writer

WORLD_SETTINGS_FILE = "world_settings.json"
WEEKLY_SCRIPT_FILE = "weekly_script.json"
QUIZ_DB = "novel_engine/data/storage/course_data.db"

def get_week_date_from_db(abs_week):
    if not os.path.exists(QUIZ_DB): return "未知日期"
    try:
        conn = sqlite3.connect(QUIZ_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT start_date FROM curriculum WHERE week=?", (abs_week,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else "未知日期"
    except: return "未知日期"

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
    
    # Prepare data structure for JSON output of compatible format
    # Prepare static data (world settings)
    world_settings = {
        "meta": {
            "title": "《拮抗中学：众生相》",
            "generated_at": time.strftime('%Y-%m-%d %H:%M:%S'),
            "description": "Static world data and character settings.",
            "system_prompt": {
                "role": "顶级爽文作家",
                "style": "维持高武侠风格，细致入微，热血沸腾",
                "background": "硬核高考修仙世界观",
                "requirements": "单章4000字，禁止烂尾，多用短句，节奏紧凑"
            }
        },
        "characters": []
    }

    # Prepare dynamic data (weekly script)
    weekly_script = {
        "meta": {
            "title": "《拮抗中学：三年因果》",
            "generated_at": time.strftime('%Y-%m-%d %H:%M:%S'),
             "description": "Dynamic weekly events and plot points."
        },
        "weeks": {}
    }

    # 1. 记录全班灵魂设定 (确保持久化一致性)
    for s in engine.students:
        world_settings["characters"].append({
            "name": s.name,
            "gender": s.gender,
            "background": s.get_soul_desc(),
            "tags": str(s.tags)
        })

    # 2. 推演 120 周
    
    for year in [1, 2, 3]:
        engine.year = year
        for semester in [1, 2]:
            engine.semester = semester
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
                
                # 构建本周数据
                date_str = f"G{year}S{semester}_W{week:02d}"
                real_date = get_week_date_from_db(abs_week)
                
                # 筛选关键剧情，兼容 main.py 的 expecting "details"
                details = []
                for l in logs:
                    if l.startswith("【突发】") or l.startswith("【战报】") or l.startswith("【道心抉择】") or l.startswith("【突破】") or "开启信奥" in l:
                        details.append(l)

                week_data = {
                    "event": battle_type,
                    "date": real_date,
                    "details": details,
                    "quiz": str(quiz_final) if quiz_final else None,
                    "rankings": {
                        "mc_report": engine.get_mc_report(),
                        "top_student": engine.get_rankings()[0].name
                    }
                }
                
                weekly_script["weeks"][date_str] = week_data

    # Save World Settings
    with open(WORLD_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(world_settings, f, ensure_ascii=False, indent=2)
    print(f"[SUCCESS] 世界观设定已刻录: {WORLD_SETTINGS_FILE}")

    # Save Weekly Script
    with open(WEEKLY_SCRIPT_FILE, "w", encoding="utf-8") as f:
        json.dump(weekly_script, f, ensure_ascii=False, indent=2)
    print(f"[SUCCESS] 三年因果剧本已刻录: {WEEKLY_SCRIPT_FILE}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="造化鼎 - 三年剧本推演工具")
    parser.add_argument("--debug", action="store_true", help="开启调试模式，输出完整 AI 提示词")
    args = parser.parse_args()
    
    if args.debug:
        writer.debug = True
        print(" [SYSTEM] 已开启调试模式，将输出完整 AI 提示词。")
        
    run_plan()
