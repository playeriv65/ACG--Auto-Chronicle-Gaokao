from __future__ import annotations

"""Character model used by the simulation engine."""

import math
import random
from typing import Dict, List, Sequence

from config import Config
from novel_engine.core.contracts import PersonProfile, PersonState, RoleType, SkillState, TraitType
from novel_engine.core.engine_constants import ALL_SUBJECTS_MARKER
from novel_engine.data.database import Subject


class Person:
    """Represents one actor (student or teacher) in the world state."""

    def __init__(
        self,
        name: str,
        role: RoleType,
        tags: List[str],
        is_male: bool,
        *,
        is_elite: bool,
        family: str,
        quirk: str,
        flaw: str,
        traits: List[TraitType] | None = None,
    ):
        self.name: str = name
        self.role: RoleType = role
        self.tags: List[str] = tags
        self.is_male: bool = is_male
        self.is_elite: bool = is_elite
        self.traits: List[TraitType] = list(traits or [])

        self.family: str = family
        self.quirk: str = quirk
        self.flaw: str = flaw

        if role == "protagonist":
            self.talent = self._build_protagonist_talent()
            self.mastery = self._build_protagonist_mastery()
        else:
            self.talent = self._build_student_talent()
            self.mastery = self._build_student_mastery()

        self.last_mastery: Dict[str, float] = self.mastery.copy()
        self.skills: List[SkillState] = []
        self.mood: int = Config.DEFAULT_MOOD
        self.stress: int = Config.DEFAULT_STRESS
        self.fatigue: int = Config.DEFAULT_FATIGUE
        self.focus_subjects: List[str] = []
        self.last_week_rank: int = Config.DEFAULT_LAST_WEEK_RANK

    INFO_TRACK_TRAIT: TraitType = "info_track"
    ELITE_TRAIT: TraitType = "elite"

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

    def _build_student_talent(self) -> Dict[str, int]:
        talent_min = Config.ELITE_TALENT_MIN if self.is_elite else Config.NORMAL_TALENT_MIN
        talent_max = Config.ELITE_TALENT_MAX if self.is_elite else Config.NORMAL_TALENT_MAX
        return {subject: random.randint(talent_min, talent_max) for subject in Subject.ALL}

    def _build_student_mastery(self) -> Dict[str, float]:
        mastery_min = Config.ELITE_MASTERY_MIN if self.is_elite else Config.NORMAL_MASTERY_MIN
        mastery_max = Config.ELITE_MASTERY_MAX if self.is_elite else Config.NORMAL_MASTERY_MAX
        return {subject: float(random.randint(mastery_min, mastery_max)) for subject in Subject.ALL}

    def to_state(self) -> PersonState:
        return PersonState(
            name=self.name,
            role=self.role,
            tags=self.tags,
            traits=self.traits,
            is_elite=self.is_elite,
            is_male=self.is_male,
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

    def has_trait(self, trait: TraitType) -> bool:
        """Business logic should branch on traits, not free-form tags."""
        return trait in self.traits

    @staticmethod
    def from_profile(profile: PersonProfile) -> "Person":
        return Person(
            profile.name,
            profile.role,
            list(profile.tags),
            profile.is_male,
            is_elite=profile.is_elite,
            family=profile.family,
            quirk=profile.quirk,
            flaw=profile.flaw,
            traits=list(profile.traits),
        )

    def to_profile(self) -> PersonProfile:
        traits: List[TraitType] = list(self.traits)
        if self.is_elite and self.ELITE_TRAIT not in traits:
            traits.append(self.ELITE_TRAIT)
        return PersonProfile(
            name=self.name,
            is_male=self.is_male,
            role=self.role,
            is_elite=self.is_elite,
            traits=traits,
            tags=list(self.tags),
            family=self.family,
            flaw=self.flaw,
            quirk=self.quirk,
        )

    @staticmethod
    def from_state(state: PersonState) -> "Person":
        person = Person(
            state.name,
            state.role,
            list(state.tags),
            state.is_male,
            is_elite=state.is_elite,
            family=state.family,
            quirk=state.quirk,
            flaw=state.flaw,
            traits=list(state.traits),
        )
        person.talent = dict(state.talent)
        person.mastery = dict(state.mastery)
        person.last_mastery = dict(state.last_mastery)
        person.skills = list(state.skills)
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
        for skill in self.skills:
            if subject in skill.name:
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

        if current_week > Config.INFO_OPTIONAL_START_WEEK and self.has_trait(self.INFO_TRACK_TRAIT) and not is_exam_week:
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

        focus_set = set(self.focus_subjects)
        for subject in Subject.ALL:
            current = self.mastery[subject]
            inhibition = 1.0 / (math.log10(current + 10.0) / 2.0)
            growth = self.talent[subject] * Config.BASE_GROWTH_FACTOR * inhibition
            if self.is_elite:
                growth *= Config.ELITE_GROWTH_MULTIPLIER
            if self.role == "protagonist" and subject == Subject.INFO:
                growth *= Config.INFO_GROWTH_MULTIPLIER

            if subject in focus_set:
                self.mastery[subject] = current + growth
                self.fatigue += Config.FOCUS_FATIGUE_COST
            else:
                self.mastery[subject] = current + growth * Config.NON_FOCUS_GROWTH_MULTIPLIER

        if self.fatigue > Config.FATIGUE_BREAKDOWN_THRESHOLD:
            self.fatigue = Config.FATIGUE_RESET_AFTER_BREAKDOWN
            for subject in self.mastery:
                self.mastery[subject] *= Config.BREAKDOWN_MASTERY_PENALTY
            return "病倒"

        return "苦修"

    def get_soul_desc(self) -> str:
        return f"[{self.family}, {self.flaw}, 喜欢{self.quirk}]"
