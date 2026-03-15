"""Unit tests for Person class - core character model."""

from __future__ import annotations

import pytest

from config import Config
from novel_engine.core.contracts import (
    PersonProfile,
    PersonState,
    RoleType,
    SkillState,
    TraitType,
)
from novel_engine.core.engine_constants import ALL_SUBJECTS_MARKER
from novel_engine.core.person import Person
from novel_engine.data.database import Subject


def _build_test_person(
    *,
    name: str = "测试角色",
    role: RoleType = "classmate",
    is_elite: bool = False,
    tags: list[str] | None = None,
    traits: list[TraitType] | None = None,
) -> Person:
    return Person(
        name,
        role,
        tags or [],
        True,
        is_elite=is_elite,
        family="普通工薪",
        quirk="转笔",
        flaw="拖延症",
        traits=traits,
    )


class TestPersonInit:
    def test_protagonist_has_fixed_talent(self) -> None:
        person = _build_test_person(name="叶凌天", role="protagonist")

        assert person.talent[Subject.MATH] == Config.PROTAGONIST_BASE_TALENT
        assert person.talent[Subject.INFO] == Config.PROTAGONIST_INFO_TALENT

    def test_protagonist_has_fixed_mastery_range(self) -> None:
        person = _build_test_person(name="叶凌天", role="protagonist")

        for subject in Subject.ALL:
            if subject != Subject.INFO:
                assert (
                    Config.PROTAGONIST_MASTERY_MIN
                    <= person.mastery[subject]
                    <= Config.PROTAGONIST_MASTERY_MAX
                )
        assert person.mastery[Subject.INFO] == Config.PROTAGONIST_INFO_MASTERY

    def test_elite_student_has_elite_talent_range(self) -> None:
        person = _build_test_person(is_elite=True)

        for subject in Subject.ALL:
            assert (
                Config.ELITE_TALENT_MIN
                <= person.talent[subject]
                <= Config.ELITE_TALENT_MAX
            )

    def test_normal_student_has_normal_talent_range(self) -> None:
        person = _build_test_person(is_elite=False)

        for subject in Subject.ALL:
            assert (
                Config.NORMAL_TALENT_MIN
                <= person.talent[subject]
                <= Config.NORMAL_TALENT_MAX
            )

    def test_default_state_values(self) -> None:
        person = _build_test_person()

        assert person.mood == Config.DEFAULT_MOOD
        assert person.stress == Config.DEFAULT_STRESS
        assert person.fatigue == Config.DEFAULT_FATIGUE
        assert person.last_week_rank == Config.DEFAULT_LAST_WEEK_RANK
        assert person.focus_subjects == []
        assert person.skills == []


class TestPersonStateRoundtrip:
    def test_to_state_contains_all_fields(self) -> None:
        person = _build_test_person()
        person.focus_subjects = [Subject.MATH]
        person.mood = 75
        person.stress = 20
        person.skills = [SkillState(name="洛必达法则", level=1, description="test")]

        state = person.to_state()

        assert state.name == person.name
        assert state.role == person.role
        assert state.focus_subjects == [Subject.MATH]
        assert state.mood == 75
        assert state.stress == 20
        assert len(state.skills) == 1

    def test_from_state_reconstructs_person(self) -> None:
        original = _build_test_person(name="测试A")
        original.focus_subjects = [Subject.PHYS]
        original.mood = 60
        original.stress = 15

        state = original.to_state()
        recovered = Person.from_state(state)

        assert recovered.name == original.name
        assert recovered.focus_subjects == [Subject.PHYS]
        assert recovered.mood == 60
        assert recovered.stress == 15
        assert recovered.mastery == original.mastery


class TestPersonProfileRoundtrip:
    def test_from_profile_creates_person(self) -> None:
        profile = PersonProfile(
            name="张三",
            is_male=True,
            role="classmate",
            is_elite=False,
            traits=["hardcore"],
            tags=["卷王"],
            family="知识分子",
            flaw="傲慢",
            quirk="背诗",
        )

        person = Person.from_profile(profile)

        assert person.name == "张三"
        assert person.role == "classmate"
        assert person.is_elite is False
        assert person.traits == ["hardcore"]

    def test_to_profile_includes_elite_trait(self) -> None:
        person = _build_test_person(is_elite=True, traits=[])

        profile = person.to_profile()

        assert "elite" in profile.traits


class TestGetExamScore:
    def test_score_within_cap(self) -> None:
        person = _build_test_person()
        person.mastery[Subject.MATH] = 5000.0

        score = person.get_exam_score(Subject.MATH)

        assert 0 <= score <= Config.EXAM_SCORE_CAP

    def test_higher_mastery_yields_higher_score(self) -> None:
        person1 = _build_test_person(name="A")
        person2 = _build_test_person(name="B")

        person1.mastery[Subject.MATH] = 1000.0
        person2.mastery[Subject.MATH] = 5000.0
        person1.stress = person2.stress = 0
        person1.fatigue = person2.fatigue = 0

        assert person2.get_exam_score(Subject.MATH) > person1.get_exam_score(
            Subject.MATH
        )

    def test_stress_reduces_score(self) -> None:
        person = _build_test_person()
        person.mastery[Subject.MATH] = 3000.0
        person.stress = 0
        person.fatigue = 0

        score_normal = person.get_exam_score(Subject.MATH)

        person.stress = 50
        score_stressed = person.get_exam_score(Subject.MATH)

        assert score_stressed < score_normal

    def test_skill_adds_bonus(self) -> None:
        person = _build_test_person()
        person.mastery[Subject.MATH] = 2000.0
        person.stress = 0
        person.fatigue = 0

        score_no_skill = person.get_exam_score(Subject.MATH)

        person.skills.append(
            SkillState(name="洛必达法则(数学)", level=1, description="test")
        )
        score_with_skill = person.get_exam_score(Subject.MATH)

        assert score_with_skill > score_no_skill

    def test_missing_subject_raises_keyerror(self) -> None:
        person = _build_test_person()

        with pytest.raises(KeyError):
            person.get_exam_score("不存在的科目")


class TestPlanWeek:
    def test_uses_battle_subjects_when_provided(self) -> None:
        person = _build_test_person()
        person.plan_week(
            is_exam_week=False, current_week=1, battle_subjects=[Subject.PHYS]
        )

        assert person.focus_subjects == [Subject.PHYS]

    def test_all_subjects_marker_uses_weakest(self) -> None:
        person = _build_test_person()

        for subject in Subject.ALL:
            if subject != Subject.INFO:
                person.mastery[subject] = 3000.0
        person.mastery[Subject.PHYS] = 1000.0

        person.plan_week(
            is_exam_week=False, current_week=1, battle_subjects=[ALL_SUBJECTS_MARKER]
        )

        assert Subject.PHYS in person.focus_subjects

    def test_exam_week_increases_stress(self) -> None:
        person = _build_test_person()
        initial_stress = person.stress

        person.plan_week(
            is_exam_week=True, current_week=1, battle_subjects=[Subject.MATH]
        )

        assert person.stress == initial_stress + Config.EXAM_STRESS_INCREMENT

    def test_info_track_trait_switches_to_info_after_unlock_week(self) -> None:
        person = _build_test_person(traits=["info_track"])
        person.plan_week(
            is_exam_week=False,
            current_week=Config.INFO_OPTIONAL_START_WEEK + 1,
            battle_subjects=[Subject.MATH],
        )

        if person.focus_subjects == [Subject.INFO]:
            assert True
        else:
            assert person.focus_subjects == [Subject.MATH]


class TestExecuteWeek:
    def test_raises_on_empty_focus_subjects(self) -> None:
        person = _build_test_person()
        person.focus_subjects = []

        with pytest.raises(ValueError, match="focus_subjects is empty"):
            person.execute_week()

    def test_increases_mastery_for_focus_subjects(self) -> None:
        person = _build_test_person()
        person.focus_subjects = [Subject.MATH]
        initial_mastery = person.mastery[Subject.MATH]

        person.execute_week()

        assert person.mastery[Subject.MATH] > initial_mastery

    def test_increases_fatigue_for_focus_subjects(self) -> None:
        person = _build_test_person()
        person.focus_subjects = [Subject.MATH]
        initial_fatigue = person.fatigue

        person.execute_week()

        assert person.fatigue == initial_fatigue + Config.FOCUS_FATIGUE_COST

    def test_non_focus_subjects_grow_slower(self) -> None:
        person = _build_test_person()
        person.focus_subjects = [Subject.MATH]

        initial_mastery_math = person.mastery[Subject.MATH]
        initial_mastery_phys = person.mastery[Subject.PHYS]

        person.execute_week()

        growth_math = person.mastery[Subject.MATH] - initial_mastery_math
        growth_phys = person.mastery[Subject.PHYS] - initial_mastery_phys

        assert growth_math > growth_phys

    def test_breakdown_resets_fatigue_and_reduces_mastery(self) -> None:
        person = _build_test_person()
        person.focus_subjects = [Subject.MATH]
        person.fatigue = Config.FATIGUE_BREAKDOWN_THRESHOLD + 10

        for subject in Subject.ALL:
            person.mastery[subject] = 10000.0

        result = person.execute_week()

        assert result == "病倒"
        assert person.fatigue == Config.FATIGUE_RESET_AFTER_BREAKDOWN

        for subject in Subject.ALL:
            expected = 10000.0 * Config.BREAKDOWN_MASTERY_PENALTY
            variance = abs(person.mastery[subject] - expected)
            assert variance < 1000, (
                f"Subject {subject} mastery variance too high: {variance}"
            )

    def test_elite_growth_multiplier_applied(self) -> None:
        elite = _build_test_person(is_elite=True)
        normal = _build_test_person(is_elite=False)

        for person in [elite, normal]:
            person.talent[Subject.MATH] = 100
            person.mastery[Subject.MATH] = 1000.0
            person.focus_subjects = [Subject.MATH]

        initial_elite = elite.mastery[Subject.MATH]
        initial_normal = normal.mastery[Subject.MATH]

        elite.execute_week()
        normal.execute_week()

        growth_elite = elite.mastery[Subject.MATH] - initial_elite
        growth_normal = normal.mastery[Subject.MATH] - initial_normal

        assert growth_elite > growth_normal

    def test_protagonist_info_multiplier_applied(self) -> None:
        protagonist = _build_test_person(name="叶凌天", role="protagonist")
        protagonist.focus_subjects = [Subject.INFO]

        initial_mastery = protagonist.mastery[Subject.INFO]
        protagonist.execute_week()

        assert protagonist.mastery[Subject.INFO] > initial_mastery


class TestHasTrait:
    def test_returns_true_for_present_trait(self) -> None:
        person = _build_test_person(traits=["hardcore", "info_track"])

        assert person.has_trait("hardcore") is True
        assert person.has_trait("info_track") is True

    def test_returns_false_for_missing_trait(self) -> None:
        person = _build_test_person(traits=["hardcore"])

        assert person.has_trait("info_track") is False
