"""Tests for BeingEngine core business logic - tick, exams, rankings."""

from __future__ import annotations

import pytest

from config import Config
from novel_engine.core.being_engine import BeingEngine
from novel_engine.core.contracts import QuizContent
from novel_engine.data.database import Subject


def _create_engine() -> BeingEngine:
    try:
        return BeingEngine()
    except ValueError as e:
        if "Duplicate person names" in str(e):
            pytest.skip("Database contains duplicate names")
        raise


class TestEngineInit:
    def test_engine_initializes_with_students(self) -> None:
        engine = _create_engine()
        assert len(engine.students) >= Config.DEFAULT_CLASSMATE_COUNT

    def test_engine_has_protagonist(self) -> None:
        engine = _create_engine()

        protagonist = next(
            (s for s in engine.students if s.role == "protagonist"), None
        )
        assert protagonist is not None
        assert protagonist.name == Config.PROTAGONIST_NAME

    def test_engine_has_rival(self) -> None:
        engine = _create_engine()

        rival = next((s for s in engine.students if s.name == Config.RIVAL_NAME), None)
        assert rival is not None

    def test_engine_has_teachers(self) -> None:
        engine = _create_engine()

        assert len(engine.teachers) > 0
        for teacher in engine.teachers:
            assert teacher.role == "teacher"


class TestEngineStateRoundtrip:
    def test_to_state_preserves_all_students(self) -> None:
        engine = _create_engine()
        state = engine.to_state()

        assert len(state.students) == len(engine.students)

    def test_from_state_reconstructs_engine(self) -> None:
        original = _create_engine()
        original.year = 2
        original.semester = 1

        state = original.to_state()

        recovered = BeingEngine()
        recovered.from_state(state)

        assert recovered.year == 2
        assert recovered.semester == 1
        assert len(recovered.students) == len(original.students)


class TestEngineTick:
    def test_tick_returns_logs_and_battle_type(self) -> None:
        engine = _create_engine()
        engine.year = 1
        engine.semester = 1

        logs, battle_type, quiz = engine.tick(week_idx=1)

        assert isinstance(logs, list)
        assert isinstance(battle_type, str)
        assert quiz is None or isinstance(quiz, QuizContent)

    def test_tick_updates_student_mastery(self) -> None:
        engine = _create_engine()
        initial_mastery = engine.students[0].mastery.copy()

        engine.tick(week_idx=1)

        changed = False
        for subject in Subject.ALL:
            if engine.students[0].mastery[subject] != initial_mastery.get(subject, 0):
                changed = True
                break
        assert changed


class TestExamScoreBoundary:
    def test_score_never_exceeds_cap(self) -> None:
        engine = _create_engine()

        for student in engine.students:
            for subject in Subject.ALL:
                score = student.get_exam_score(subject)
                assert 0 <= score <= Config.EXAM_SCORE_CAP, (
                    f"{student.name} {subject}: {score}"
                )

    def test_zero_mastery_yields_low_score(self) -> None:
        engine = _create_engine()
        student = engine.students[0]

        for subject in Subject.ALL:
            student.mastery[subject] = 0.0

        score = student.get_exam_score(Subject.MATH)
        assert score < 50

    def test_max_stress_reduces_score_significantly(self) -> None:
        engine = _create_engine()
        student = engine.students[0]
        student.mastery[Subject.MATH] = 5000.0
        student.stress = 0
        student.fatigue = 0

        score_normal = student.get_exam_score(Subject.MATH)

        student.stress = 100
        student.fatigue = 100
        score_stressed = student.get_exam_score(Subject.MATH)

        assert score_stressed < score_normal


class TestRankings:
    def test_rankings_populated_after_tick(self) -> None:
        engine = _create_engine()
        engine.tick(week_idx=1)

        assert len(engine.rankings) > 0

    def test_protagonist_in_rankings(self) -> None:
        engine = _create_engine()
        engine.tick(week_idx=1)

        protagonist_names = [s.name for s in engine.students if s.role == "protagonist"]
        ranking_names = [s.name for s in engine.rankings]

        for name in protagonist_names:
            assert name in ranking_names


class TestSocialGraph:
    def test_social_graph_is_symmetric(self) -> None:
        engine = _create_engine()

        for src, row in engine.social_graph.items():
            for dst, score in row.items():
                assert src != dst
                assert engine.social_graph[dst][src] == score

    def test_social_graph_values_in_valid_range(self) -> None:
        engine = _create_engine()

        for src, row in engine.social_graph.items():
            for dst, score in row.items():
                assert Config.RELATION_MIN <= score <= Config.RELATION_MAX


class TestBuildQuizPromptPayload:
    def test_returns_none_for_none_quiz(self) -> None:
        engine = _create_engine()

        result = engine.build_quiz_prompt_payload(None)

        assert result is None

    def test_returns_string_for_valid_quiz(self) -> None:
        engine = _create_engine()
        quiz = QuizContent(
            kind="direct", subject=Subject.MATH, topic="函数", content="test question"
        )

        result = engine.build_quiz_prompt_payload(quiz)

        assert result is not None
        assert "test question" in result

    def test_fallback_quiz_requires_subject_and_topic(self) -> None:
        engine = _create_engine()
        quiz = QuizContent(kind="fallback", subject=None, topic=None, content=None)

        with pytest.raises(
            ValueError, match="Fallback quiz content requires subject and topic"
        ):
            engine.build_quiz_prompt_payload(quiz)


class TestFatigueAndBreakdown:
    def test_fatigue_increases_during_focus(self) -> None:
        engine = _create_engine()
        student = engine.students[0]
        initial_fatigue = student.fatigue

        student.focus_subjects = [Subject.MATH]
        student.execute_week()

        assert student.fatigue > initial_fatigue

    def test_breakdown_resets_fatigue(self) -> None:
        engine = _create_engine()
        student = engine.students[0]
        student.fatigue = Config.FATIGUE_BREAKDOWN_THRESHOLD + 20
        student.focus_subjects = [Subject.MATH]

        student.execute_week()

        assert student.fatigue == Config.FATIGUE_RESET_AFTER_BREAKDOWN
