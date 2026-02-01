
import sqlite3
import os
from novel_engine.data.database import Subject

DB_PATH = "novel_engine/data/storage/course_data.db"

class QuizDatabase:
    @staticmethod
    def get_quiz(subject, topic):
        # 1. 尝试从文曲库读取 AI 已命制的题目
        if os.path.exists(DB_PATH):
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT content FROM quiz WHERE subject=? AND topic=? ORDER BY RANDOM() LIMIT 1", (subject, topic))
                row = cursor.fetchone()
                conn.close()
                if row and row[0]:
                     return row[0] # 返回题目文本
            except: 
                pass

        # 2. 如果库中无题，返回指令让上层调用 AI 生成
        return {
            "type": "AI_GENERATED",
            "subject": subject,
            "topic": topic
        }