from __future__ import annotations

"""Character model used by the simulation engine."""

import math
import random
from typing import Any, Dict, List, Sequence, Tuple

from config import Config
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

        if role == "主角":
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

    def to_dict(self) -> Dict[str, Any]:
        """Serialize runtime fields for save-state persistence."""
        d = self.__dict__.copy()
        d["mastery"] = {k: v for k, v in self.mastery.items()}
        d["talent"] = {k: v for k, v in self.talent.items()}
        d["last_mastery"] = {k: v for k, v in self.last_mastery.items()}
        d["focus_subjects"] = list(self.focus_subjects)
        return d

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Person":
        """Rehydrate a Person from persisted dictionary data."""
        p = Person(data["name"], data["role"], data["tags"], data["gender"])
        for k, v in data.items():
            if k in ["mastery", "talent", "last_mastery"]:
                setattr(p, k, {key: val for key, val in v.items()})
            else:
                setattr(p, k, v)
        return p

    def get_exam_score(self, subject: str) -> int:
        """Compute score with mastery, talent, pressure and skill bonuses."""
        # Score is intentionally capped/scaled to exam range after all modifiers are applied.
        base = self.mastery.get(subject, 0.0)
        penalty = (self.stress + self.fatigue) / Config.EXAM_PENALTY_DIVISOR
        talent_mod = self.talent.get(subject, Config.DEFAULT_SUBJECT_TALENT) / 100.0

        skill_bonus = 0.0
        for n, _lvl, _d in self.skills:
            if subject in n:
                skill_bonus += Config.SKILL_SUBJECT_BONUS

        score = (base + skill_bonus) * talent_mod * (1.0 - penalty)
        return int(min(Config.EXAM_SCORE_CAP, score / Config.EXAM_SCORE_DIVISOR))

    def plan_week(self, is_exam_week: bool, current_week: int, battle_subjects: Sequence[str]) -> None:
        """Pick focus subjects for current week and update stress state."""
        # Prefer explicit battle subjects; otherwise auto-focus weakest non-info subject.
        if battle_subjects and "全科" not in battle_subjects:
            self.focus_subjects = list(battle_subjects)
        else:
            scores = {s: self.mastery.get(s, 0.0) for s in Subject.ALL if s != Subject.INFO}
            weakest = min(scores, key=lambda subject: scores[subject]) if scores else Subject.MATH
            self.focus_subjects = [weakest]

        if is_exam_week:
            self.stress += Config.EXAM_STRESS_INCREMENT

        if current_week > Config.INFO_OPTIONAL_START_WEEK and "信奥党" in self.tags and not is_exam_week:
            if random.random() < Config.INFO_OPTIONAL_FOCUS_PROB:
                self.focus_subjects = [Subject.INFO]

    def execute_week(self) -> str:
        """Advance one week of study and return status label."""
        # Apply focused growth first, then passive growth, and finally fatigue breakdown penalties.
        self.last_mastery = self.mastery.copy()

        def calc_growth(subj: str) -> float:
            current = self.mastery.get(subj, 0.0)
            inhibition = 1.0 / (math.log10(current + 10.0) / 2.0)
            talent_val = self.talent.get(subj, Config.DEFAULT_SUBJECT_TALENT)
            growth = talent_val * Config.BASE_GROWTH_FACTOR * inhibition

            if "卷王" in self.tags:
                growth *= Config.ELITE_GROWTH_MULTIPLIER
            if self.role == "主角" and subj == Subject.INFO:
                growth *= Config.INFO_GROWTH_MULTIPLIER
            return growth

        for s in self.focus_subjects:
            self.mastery[s] = self.mastery.get(s, 0.0) + calc_growth(s)
            self.fatigue += Config.FOCUS_FATIGUE_COST

        for s in Subject.ALL:
            if s not in self.focus_subjects:
                self.mastery[s] = self.mastery.get(s, 0.0) + calc_growth(s) * Config.NON_FOCUS_GROWTH_MULTIPLIER

        if self.fatigue > Config.FATIGUE_BREAKDOWN_THRESHOLD:
            self.fatigue = Config.FATIGUE_RESET_AFTER_BREAKDOWN
            for k in self.mastery:
                self.mastery[k] *= Config.BREAKDOWN_MASTERY_PENALTY
            return "病倒"

        return "苦修"

    def get_soul_desc(self) -> str:
        """Compact flavor text used by plan/script builders."""
        return f"[{self.family}, {self.flaw}, 喜欢{self.quirk}]"
