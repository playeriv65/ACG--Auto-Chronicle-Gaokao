from __future__ import annotations

import os
import sqlite3

from novel_engine.core.contracts import QuizContent

DB_PATH = "novel_engine/data/storage/course_data.db"


class QuizDatabase:
    @staticmethod
    def get_quiz(subject: str, topic: str) -> QuizContent:
        if os.path.exists(DB_PATH):
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT content FROM quiz WHERE subject=? AND topic=? ORDER BY RANDOM() LIMIT 1",
                    (subject, topic),
                )
                row = cursor.fetchone()
                if row and row[0]:
                    return QuizContent(kind="direct", content=str(row[0]))

        return QuizContent(kind="fallback", subject=subject, topic=topic)
