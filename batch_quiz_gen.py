import sys
import os
import sqlite3
import time
import math
sys.path.append(os.getcwd())

from novel_engine.data.curriculum_data import Curriculum
from novel_engine.core.ai_writer import writer
from novel_engine.data.database import Subject

DB_PATH = "novel_engine/data/quiz_bank.db"
LOG_FILE = "quiz_gen_final.log"

def write_log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    formatted = f"[{timestamp}] {msg}"
    # 写入文件 (此为日志真身)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")
    # 仅在交互式终端打印，避免 nohup 重定向产生重影
    if sys.stdout.isatty():
        print(formatted)

def get_db_conn():
    return sqlite3.connect(DB_PATH)

def check_exists(week, subject, topic):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM quiz WHERE week=? AND subject=? AND topic=?", (week, subject, topic))
    res = cursor.fetchone()
    conn.close()
    return res is not None

def save_quiz(week, subject, topic, content):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO quiz (week, subject, topic, content) VALUES (?, ?, ?, ?)", (week, subject, topic, content))
    conn.commit()
    conn.close()

def run_batch():
    write_log("🚀 [天库大阵] 开始执行持久化命题任务...")
    
    target_subjects = [Subject.MATH, Subject.PHYS, Subject.CHEM, Subject.BIO, Subject.ENG, Subject.CHN]
    
    for abs_week in range(1, 41):
        year = 1
        semester = 1 if abs_week <= 20 else 2
        week = abs_week if semester == 1 else abs_week - 20
        
        curriculum = Curriculum.get_weekly_content(year, semester, week)
        
        for subj in target_subjects:
            topic = curriculum.get(subj)
            if not topic or "假期" in topic: continue
            
            if check_exists(abs_week, subj, topic): continue
            
            write_log(f"Processing Week {abs_week:02d} | {subj}: {topic}")
            
            success = False
            for attempt in range(3):
                try:
                    # 强加超时逻辑在 AI 调用层（如果 writer 已支持）
                    # 这里直接调用
                    content = writer.generate_quiz(subj, topic)
                    if content and len(content) > 1: # 放宽限制，只要有气就行
                        save_quiz(abs_week, subj, topic, content)
                        write_log(f"  [SUCCESS] {subj} 已入库")
                        success = True
                        break
                    else:
                        write_log(f"  [EMPTY] 返回内容太短或为空: {content}")
                        time.sleep(10)
                except Exception as e:
                    write_log(f"  [ERROR] {e}")
                    time.sleep(15)
            
            if not success: write_log(f"  [FAILED] {subj} 跳过")
            time.sleep(3) 

    write_log("✅ [天库大阵] 功德圆满。")

if __name__ == "__main__":
    run_batch()
