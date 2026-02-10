from __future__ import annotations

import json
import random
import sqlite3
from typing import Any, Dict, List, Optional, Sequence, Tuple

DB_PATH = "novel_engine/data/storage/world_data.db"
SkillTuple = Tuple[str, int, str]
EventTuple = Tuple[str, str]
ArchetypeTuple = Tuple[str, str, Dict[str, Any]]
TeacherProfileTuple = Tuple[str, str]
_DEFAULT_NAMES: Tuple[str, ...] = ("李", "王", "张")
_DEFAULT_WEIGHTS: Tuple[int, ...] = (1, 1, 1)
_DEFAULT_FALLBACKS: Dict[str, Sequence[str]] = {
    "families": ("普通工薪",),
    "quirks": ("转笔",),
    "flaws": ("拖延症",),
}

class Subject:
    MATH, PHYS, CHEM, BIO, ENG, CHN, INFO, HIST, GEO, POLI = "数学", "物理", "化学", "生物", "英语", "语文", "信奥", "历史", "地理", "政治"
    ALL: List[str] = [MATH, PHYS, CHEM, BIO, ENG, CHN, INFO, HIST, GEO, POLI]

class DBConnector:
    @staticmethod
    def get_connection() -> sqlite3.Connection:
        return sqlite3.connect(DB_PATH)

# Helper for class-level properties
class classproperty:
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)

class SkillTree:
    @staticmethod
    def get_skill_by_subject(subject: str, mastery_val: float) -> SkillTuple:
        conn = DBConnector.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name, level, description FROM skills WHERE subject = ? ORDER BY level", (subject,))
            skills = cursor.fetchall()
            if not skills:
                return ("基础知识", 1, "平平无奇")
            
            # mastery 1000 = level 1, 2000 = level 2...
            idx = min(len(skills) - 1, max(0, int(mastery_val // 1000) - 1))
            unlocked = skills[: idx + 1]
            return random.choice(unlocked) if unlocked else ("基础知识", 1, "平平无奇")
        finally:
            conn.close()


def get_random_event(season: str = "ANY") -> EventTuple:
    conn = DBConnector.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT description, effect FROM events WHERE season = 'ANY' OR season = ?", (season,))
        events = cursor.fetchall()
        if not events:
            return ("发呆", "")
        return random.choice(events)
    finally:
        conn.close()

class NPCData:
    _SURNAMES_CACHE: Optional[Sequence[str]] = None
    _SURNAMES_WEIGHTS_CACHE: Optional[Sequence[float]] = None
    
    _ARCHETYPES_CACHE: Optional[List[ArchetypeTuple]] = None
    _TEACHER_PROFILES_CACHE: Optional[List[TeacherProfileTuple]] = None
    _FAMILIES_CACHE: Optional[List[str]] = None
    _QUIRKS_CACHE: Optional[List[str]] = None
    _FLAWS_CACHE: Optional[List[str]] = None

    @classmethod
    def _fetch_all(cls, query: str, params: Sequence[object] = ()) -> List[Tuple[Any, ...]]:
        conn = DBConnector.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            conn.close()

    @classmethod
    def get_name(cls, gender: str = "M", era: str = "00s") -> str:
        if cls._SURNAMES_CACHE is None:
            rows = cls._fetch_all("SELECT name, frequency FROM surnames")
            if rows:
                cls._SURNAMES_CACHE, cls._SURNAMES_WEIGHTS_CACHE = zip(*rows)
            else:
                cls._SURNAMES_CACHE = _DEFAULT_NAMES
                cls._SURNAMES_WEIGHTS_CACHE = _DEFAULT_WEIGHTS
        
        surname = random.choices(cls._SURNAMES_CACHE, weights=cls._SURNAMES_WEIGHTS_CACHE, k=1)[0]
        
        conn = DBConnector.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM given_names WHERE gender = ? AND era = ? ORDER BY RANDOM() LIMIT 1", (gender, era))
            if not (res := cursor.fetchone()):
                cursor.execute("SELECT name FROM given_names WHERE gender = ? ORDER BY RANDOM() LIMIT 1", (gender,))
                res = cursor.fetchone()
            
            if not res:
                return surname + ("强" if gender == "M" else "珍")
            return surname + res[0]
        finally:
            conn.close()

    @classmethod
    def get_archetype(cls) -> ArchetypeTuple:
        if cls._ARCHETYPES_CACHE is None:
            rows = cls._fetch_all("SELECT name, title, base_stats FROM archetypes")
            cls._ARCHETYPES_CACHE = [(r[0], r[1], json.loads(r[2])) for r in rows]
        if not cls._ARCHETYPES_CACHE:
            return ("透明人", "凡人", {"stress": 40})
        return random.choice(cls._ARCHETYPES_CACHE)

    @classmethod
    def get_teacher_profile(cls) -> TeacherProfileTuple:
        if cls._TEACHER_PROFILES_CACHE is None:
            cls._TEACHER_PROFILES_CACHE = [tuple(row) for row in cls._fetch_all("SELECT subject, catchphrase FROM teacher_profiles")]  # type: ignore[list-item]
        if not cls._TEACHER_PROFILES_CACHE:
            return ("数学", "口头禅：送分题")
        return random.choice(cls._TEACHER_PROFILES_CACHE)

    @classmethod
    def get_family(cls) -> str:
        if cls._FAMILIES_CACHE is None:
            cls._FAMILIES_CACHE = [r[0] for r in cls._fetch_all("SELECT name FROM families")]
        if not cls._FAMILIES_CACHE:
            return random.choice(_DEFAULT_FALLBACKS["families"])
        return random.choice(cls._FAMILIES_CACHE)

    @classmethod
    def get_quirk(cls) -> str:
        if cls._QUIRKS_CACHE is None:
            cls._QUIRKS_CACHE = [r[0] for r in cls._fetch_all("SELECT name FROM quirks")]
        if not cls._QUIRKS_CACHE:
            return random.choice(_DEFAULT_FALLBACKS["quirks"])
        return random.choice(cls._QUIRKS_CACHE)

    @classmethod
    def get_flaw(cls) -> str:
        if cls._FLAWS_CACHE is None:
            cls._FLAWS_CACHE = [r[0] for r in cls._fetch_all("SELECT name FROM flaws")]
        if not cls._FLAWS_CACHE:
            return random.choice(_DEFAULT_FALLBACKS["flaws"])
        return random.choice(cls._FLAWS_CACHE)

    @classproperty
    def ARCHETYPES(cls) -> List[ArchetypeTuple]:
        if cls._ARCHETYPES_CACHE is None:
            cls.get_archetype()
        return cls._ARCHETYPES_CACHE or [("透明人", "凡人", {"stress": 40})]

    @classproperty
    def TEACHER_PROFILES(cls) -> List[TeacherProfileTuple]:
        if cls._TEACHER_PROFILES_CACHE is None:
            cls.get_teacher_profile()
        return cls._TEACHER_PROFILES_CACHE or [("数学", "口头禅：送分题")]

    @classproperty
    def FAMILIES(cls) -> List[str]:
        if cls._FAMILIES_CACHE is None:
            cls.get_family()
        return cls._FAMILIES_CACHE or list(_DEFAULT_FALLBACKS["families"])

    @classproperty
    def QUIRKS(cls) -> List[str]:
        if cls._QUIRKS_CACHE is None:
            cls.get_quirk()
        return cls._QUIRKS_CACHE or list(_DEFAULT_FALLBACKS["quirks"])

    @classproperty
    def FLAWS(cls) -> List[str]:
        if cls._FLAWS_CACHE is None:
            cls.get_flaw()
        return cls._FLAWS_CACHE or list(_DEFAULT_FALLBACKS["flaws"])
