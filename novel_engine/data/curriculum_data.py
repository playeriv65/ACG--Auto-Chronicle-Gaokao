
import sqlite3
import os
from novel_engine.data.database import Subject

DB_PATH = "novel_engine/data/storage/course_data.db"

class Curriculum:
    @staticmethod
    def get_weekly_content(year, semester, week):
        # 绝对周次计算: 每个学期20周
        abs_week = (year - 1) * 40 + (semester - 1) * 20 + week
        
        # 1. 尝试从数据库读取宗主的详尽课表
        if os.path.exists(DB_PATH):
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                # 检查表是否存在
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='curriculum'")
                if cursor.fetchone():
                    cursor.execute("SELECT chn, math, eng, phys, chem, bio, hist, geo, poli FROM curriculum WHERE week=?", (abs_week,))
                    row = cursor.fetchone()
                    conn.close()
                    if row:
                        return {
                            Subject.CHN: row[0],
                            Subject.MATH: row[1],
                            Subject.ENG: row[2],
                            Subject.PHYS: row[3],
                            Subject.CHEM: row[4],
                            Subject.BIO: row[5],
                            Subject.HIST: row[6],
                            Subject.GEO: row[7],
                            Subject.POLI: row[8]
                        }
            except Exception as e:
                print(f" [Curriculum DB Error] {e}")
        
        # 2. 如果数据库不可用，回退至基础逻辑 (兜底)
        return {
            "ALL": "自主复习",
            "DESC": "查漏补缺 (数据库未就位或此周无记录)"
        }
