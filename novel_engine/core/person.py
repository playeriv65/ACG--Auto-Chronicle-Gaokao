from __future__ import annotations

"""Character model used by the simulation engine."""

import math
import random
from typing import Dict, List, Sequence, Tuple

from config import Config
from novel_engine.core.contracts import PersonState
from novel_engine.core.engine_constants import ALL_SUBJECTS_MARKER, INFO_TRACK_TAG, PROTAGONIST_ROLE
from novel_engine.data.database import NPCData, Subject

Skill = Tuple[str, int, str]


class Person:
    """Represents one actor (student or teacher) in the world state."""

    def __init__(self, name: str, role: str, tags: List[str], gender: str = "男"):
        self.name: str = name
        self.role: str = role
        self.tags: List[str] = tags
        self.gender: str = gender

        self.family: str = NPCData.get_family()
        self.quirk: str = NPCData.get_quirk()
        self.flaw: str = NPCData.get_flaw()

        if role == PROTAGONIST_ROLE:
            self.talent = self._build_protagonist_talent()
            self.mastery = self._build_protagonist_mastery()
        else:
            self.talent = self._build_student_talent(tags)
            self.mastery = self._build_student_mastery(tags)

        self.last_mastery: Dict[str, float] = self.mastery.copy()
        self.skills: List[Skill] = []
        self.mood: int = Config.DEFAULT_MOOD
        self.stress: int = Config.DEFAULT_STRESS
        self.fatigue: int = Config.DEFAULT_FATIGUE
        self.focus_subjects: List[str] = []
        self.last_week_rank: int = Config.DEFAULT_LAST_WEEK_RANK

    def _build_protagonist_talent(self) -> Dict[str, int]:
        talent = {subject: Config.PROTAGONIST_BASE_TALENT for subject in Subject.ALL}
        talent[Subject.INFO] = Config.PROTAGONIST_INFO_TALENT
        return talent

    def _build_protagonist_mastery(self) -> Dict[str, float]:
        mastery = {
            subject: float(random.randint(Config.PROTAGONIST_MASTERY_MIN, Config.PROTAGONIST_MASTERY_MAX))
            for subject in Subject.ALL
        }
        mastery[Subject.INFO] = Config.PROTAGONIST_INFO_MASTERY
        return mastery

    def _build_student_talent(self, tags: Sequence[str]) -> Dict[str, int]:
        is_elite = any(tag in Config.ELITE_TAGS for tag in tags)
        talent_min = Config.ELITE_TALENT_MIN if is_elite else Config.NORMAL_TALENT_MIN
        talent_max = Config.ELITE_TALENT_MAX if is_elite else Config.NORMAL_TALENT_MAX
        return {subject: random.randint(talent_min, talent_max) for subject in Subject.ALL}

    def _build_student_mastery(self, tags: Sequence[str]) -> Dict[str, float]:
        is_elite = any(tag in Config.ELITE_TAGS for tag in tags)
        mastery_min = Config.ELITE_MASTERY_MIN if is_elite else Config.NORMAL_MASTERY_MIN
        mastery_max = Config.ELITE_MASTERY_MAX if is_elite else Config.NORMAL_MASTERY_MAX
        return {subject: float(random.randint(mastery_min, mastery_max)) for subject in Subject.ALL}

    def to_state(self) -> PersonState:
        return PersonState(
            name=self.name,
            role=self.role,
            tags=self.tags,
            gender=self.gender,
            family=self.family,
            quirk=self.quirk,
            flaw=self.flaw,
            talent=self.talent,
            mastery=self.mastery,
            last_mastery=self.last_mastery,
            skills=self.skills,
            mood=self.mood,
            stress=self.stress,
            fatigue=self.fatigue,
            focus_subjects=self.focus_subjects,
            last_week_rank=self.last_week_rank,
        )

    @staticmethod
    def from_state(state: PersonState) -> "Person":
        person = Person(state.name, state.role, list(state.tags), state.gender)
        person.family = state.family
        person.quirk = state.quirk
        person.flaw = state.flaw
        person.talent = dict(state.talent)
        person.mastery = dict(state.mastery)
        person.last_mastery = dict(state.last_mastery)
        person.skills = [(skill[0], skill[1], skill[2]) for skill in state.skills]
        person.mood = state.mood
        person.stress = state.stress
        person.fatigue = state.fatigue
        person.focus_subjects = list(state.focus_subjects)
        person.last_week_rank = state.last_week_rank
        return person

    def get_exam_score(self, subject: str) -> int:
        if subject not in self.mastery:
            raise KeyError(f"Missing mastery for subject: {subject}")
        if subject not in self.talent:
            raise KeyError(f"Missing talent for subject: {subject}")

        base = self.mastery[subject]
        penalty = (self.stress + self.fatigue) / Config.EXAM_PENALTY_DIVISOR
        talent_mod = self.talent[subject] / 100.0

        skill_bonus = 0.0
        for name, _lvl, _desc in self.skills:
            if subject in name:
                skill_bonus += Config.SKILL_SUBJECT_BONUS

        score = (base + skill_bonus) * talent_mod * (1.0 - penalty)
        return int(min(Config.EXAM_SCORE_CAP, score / Config.EXAM_SCORE_DIVISOR))

    def plan_week(self, is_exam_week: bool, current_week: int, battle_subjects: Sequence[str]) -> None:
        if battle_subjects and ALL_SUBJECTS_MARKER not in battle_subjects:
            self.focus_subjects = list(battle_subjects)
        else:
            scores = {subject: self.mastery[subject] for subject in Subject.ALL if subject != Subject.INFO}
            if not scores:
                raise ValueError(f"No score candidates for {self.name}")
            weakest = min(scores, key=lambda subject: scores[subject])
            self.focus_subjects = [weakest]

        if is_exam_week:
            self.stress += Config.EXAM_STRESS_INCREMENT

        if current_week > Config.INFO_OPTIONAL_START_WEEK and INFO_TRACK_TAG in self.tags and not is_exam_week:
            if random.random() < Config.INFO_OPTIONAL_FOCUS_PROB:
                self.focus_subjects = [Subject.INFO]

    def execute_week(self) -> str:
        if not self.focus_subjects:
            raise ValueError(f"focus_subjects is empty for {self.name}")

        missing_mastery = [subject for subject in Subject.ALL if subject not in self.mastery]
        if missing_mastery:
            raise KeyError(f"Missing mastery keys for {self.name}: {missing_mastery}")

        missing_talent = [subject for subject in Subject.ALL if subject not in self.talent]
        if missing_talent:
            raise KeyError(f"Missing talent keys for {self.name}: {missing_talent}")

        self.last_mastery = self.mastery.copy()

        for subject in self.focus_subjects:
            current = self.mastery[subject]
            inhibition = 1.0 / (math.log10(current + 10.0) / 2.0)
            growth = self.talent[subject] * Config.BASE_GROWTH_FACTOR * inhibition
            if "卷王" in self.tags:
                growth *= Config.ELITE_GROWTH_MULTIPLIER
            if self.role == PROTAGONIST_ROLE and subject == Subject.INFO:
                growth *= Config.INFO_GROWTH_MULTIPLIER
            self.mastery[subject] = current + growth
            self.fatigue += Config.FOCUS_FATIGUE_COST

        for subject in Subject.ALL:
            if subject in self.focus_subjects:
                continue
            current = self.mastery[subject]
            inhibition = 1.0 / (math.log10(current + 10.0) / 2.0)
            growth = self.talent[subject] * Config.BASE_GROWTH_FACTOR * inhibition
            if "卷王" in self.tags:
                growth *= Config.ELITE_GROWTH_MULTIPLIER
            if self.role == PROTAGONIST_ROLE and subject == Subject.INFO:
                growth *= Config.INFO_GROWTH_MULTIPLIER
            self.mastery[subject] = current + growth * Config.NON_FOCUS_GROWTH_MULTIPLIER

        if self.fatigue > Config.FATIGUE_BREAKDOWN_THRESHOLD:
            self.fatigue = Config.FATIGUE_RESET_AFTER_BREAKDOWN
            for subject in self.mastery:
                self.mastery[subject] *= Config.BREAKDOWN_MASTERY_PENALTY
            return "病倒"

        return "苦修"

    def get_soul_desc(self) -> str:
        return f"[{self.family}, {self.flaw}, 喜欢{self.quirk}]"
