import sqlite3
import os

DB_PATH = "novel_engine/data/quiz_bank.db"

def init_db():
    if not os.path.exists("novel_engine/data"):
        os.makedirs("novel_engine/data")
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建题目表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        week INTEGER,
        subject TEXT,
        topic TEXT,
        content TEXT,
        UNIQUE(week, subject, topic)
    )
    """)
    conn.commit()
    conn.close()
    print(f"[SUCCESS] 题目天书 {DB_PATH} 已铸就。")

if __name__ == "__main__":
    init_db()
