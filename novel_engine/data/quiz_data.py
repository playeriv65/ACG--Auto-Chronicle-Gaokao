from __future__ import annotations

import os
import sqlite3

from pydantic import ConfigDict

from novel_engine.core.contracts import StrictModel

DB_PATH = "novel_engine/data/storage/course_data.db"


class QuizContentModel(StrictModel):
    type: str = "QUIZ_CONTENT"
    content: str


class AIQuizFallbackModel(StrictModel):
    model_config = ConfigDict(extra="forbid")
    type: str = "AI_GENERATED"
    subject: str
    topic: str


QuizResult = QuizContentModel | AIQuizFallbackModel


class QuizDatabase:
    @staticmethod
    def get_quiz(subject: str, topic: str) -> QuizResult:
        if os.path.exists(DB_PATH):
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT content FROM quiz WHERE subject=? AND topic=? ORDER BY RANDOM() LIMIT 1",
                    (subject, topic),
                )
                row = cursor.fetchone()
                if row and row[0]:
                    return QuizContentModel(content=str(row[0]))

        return AIQuizFallbackModel(subject=subject, topic=topic)
