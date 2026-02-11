from __future__ import annotations

from config import Config
from novel_engine.core.person import Person
from novel_engine.data.database import Subject


def _build_person(*, is_elite: bool, tags: list[str]) -> Person:
    return Person(
        "测试角色",
        "classmate",
        tags,
        True,
        is_elite=is_elite,
        family="普通工薪",
        quirk="转笔",
        flaw="拖延症",
        traits=[],
    )


def test_elite_init_range_depends_on_is_elite_not_tags() -> None:
    tagged_but_not_elite = _build_person(is_elite=False, tags=["卷王", "天赋怪"])
    elite_without_tags = _build_person(is_elite=True, tags=[])

    assert all(Config.NORMAL_TALENT_MIN <= v <= Config.NORMAL_TALENT_MAX for v in tagged_but_not_elite.talent.values())
    assert all(Config.ELITE_TALENT_MIN <= v <= Config.ELITE_TALENT_MAX for v in elite_without_tags.talent.values())


def test_elite_growth_multiplier_depends_on_is_elite_not_tags() -> None:
    tagged_but_not_elite = _build_person(is_elite=False, tags=["卷王"])
    elite_without_tags = _build_person(is_elite=True, tags=[])

    for subject in Subject.ALL:
        tagged_but_not_elite.talent[subject] = 80
        tagged_but_not_elite.mastery[subject] = 500.0
        elite_without_tags.talent[subject] = 80
        elite_without_tags.mastery[subject] = 500.0

    tagged_but_not_elite.focus_subjects = [Subject.MATH]
    elite_without_tags.focus_subjects = [Subject.MATH]

    tagged_but_not_elite.execute_week()
    elite_without_tags.execute_week()

    assert elite_without_tags.mastery[Subject.MATH] > tagged_but_not_elite.mastery[Subject.MATH]
