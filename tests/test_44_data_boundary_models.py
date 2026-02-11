from __future__ import annotations

from novel_engine.core.contracts import CurriculumWeek, QuizContent
from novel_engine.core.engine_io import get_curriculum_from_db
from novel_engine.data.quiz_data import QuizDatabase


def test_engine_io_returns_curriculum_model() -> None:
    week = get_curriculum_from_db("novel_engine/data/storage/course_data.db", 1)
    assert isinstance(week, CurriculumWeek)
    assert week.abs_week == 1
    assert week.subjects


def test_quiz_database_returns_quiz_content_model() -> None:
    result = QuizDatabase.get_quiz("化学", "必修一 1.1 物质的分类与转化")
    assert isinstance(result, QuizContent)
    assert result.kind in {"direct", "fallback"}
