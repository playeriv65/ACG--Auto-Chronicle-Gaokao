from __future__ import annotations

import json
import random
import sqlite3
from typing import Any, ClassVar, Sequence

from novel_engine.core.contracts import StrictModel

DB_PATH = "novel_engine/data/storage/world_data.db"


class Subject:
    MATH, PHYS, CHEM, BIO, ENG, CHN, INFO, HIST, GEO, POLI = (
        "数学",
        "物理",
        "化学",
        "生物",
        "英语",
        "语文",
        "信奥",
        "历史",
        "地理",
        "政治",
    )
    ALL: list[str] = [MATH, PHYS, CHEM, BIO, ENG, CHN, INFO, HIST, GEO, POLI]


class SkillRecord(StrictModel):
    name: str
    level: int
    description: str


class EventRecord(StrictModel):
    description: str
    effect: str


class ArchetypeRecord(StrictModel):
    name: str
    title: str
    base_stats: dict[str, Any]


class TeacherProfileRecord(StrictModel):
    subject: str
    catchphrase: str


class DBConnector:
    @staticmethod
    def get_connection() -> sqlite3.Connection:
        return sqlite3.connect(DB_PATH)


class classproperty:
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)


class SkillTree:
    @staticmethod
    def get_skill_by_subject(subject: str, mastery_val: float) -> SkillRecord:
        conn = DBConnector.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name, level, description FROM skills WHERE subject = ? ORDER BY level", (subject,))
            rows = cursor.fetchall()
            if not rows:
                raise ValueError(f"No skills found for subject: {subject}")

            skills = [SkillRecord(name=r[0], level=int(r[1]), description=r[2]) for r in rows]
            idx = min(len(skills) - 1, max(0, int(mastery_val // 1000) - 1))
            unlocked = skills[: idx + 1]
            return random.choice(unlocked)
        finally:
            conn.close()


def get_random_event(season: str = "ANY") -> EventRecord:
    conn = DBConnector.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT description, effect FROM events WHERE season = 'ANY' OR season = ?", (season,))
        rows = cursor.fetchall()
        if not rows:
            raise ValueError(f"No events found for season: {season}")
        chosen = random.choice(rows)
        return EventRecord(description=chosen[0], effect=chosen[1])
    finally:
        conn.close()


class NPCData:
    _SURNAMES_CACHE: ClassVar[Sequence[str] | None] = None
    _SURNAMES_WEIGHTS_CACHE: ClassVar[Sequence[float] | None] = None

    _ARCHETYPES_CACHE: ClassVar[list[ArchetypeRecord] | None] = None
    _TEACHER_PROFILES_CACHE: ClassVar[list[TeacherProfileRecord] | None] = None
    _FAMILIES_CACHE: ClassVar[list[str] | None] = None
    _QUIRKS_CACHE: ClassVar[list[str] | None] = None
    _FLAWS_CACHE: ClassVar[list[str] | None] = None

    @classmethod
    def _fetch_all(cls, query: str, params: Sequence[object] = ()) -> list[tuple[Any, ...]]:
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
            if not rows:
                raise ValueError("No surnames found in DB")
            cls._SURNAMES_CACHE, cls._SURNAMES_WEIGHTS_CACHE = zip(*rows)

        surname = random.choices(cls._SURNAMES_CACHE, weights=cls._SURNAMES_WEIGHTS_CACHE, k=1)[0]

        conn = DBConnector.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM given_names WHERE gender = ? AND era = ? ORDER BY RANDOM() LIMIT 1", (gender, era))
            res = cursor.fetchone()
            if not res:
                raise ValueError(f"No given_names found for gender={gender} era={era}")
            return surname + res[0]
        finally:
            conn.close()

    @classmethod
    def get_archetype(cls) -> ArchetypeRecord:
        if cls._ARCHETYPES_CACHE is None:
            rows = cls._fetch_all("SELECT name, title, base_stats FROM archetypes")
            if not rows:
                raise ValueError("No archetypes found in DB")
            cls._ARCHETYPES_CACHE = [
                ArchetypeRecord(name=r[0], title=r[1], base_stats=json.loads(r[2]))
                for r in rows
            ]
        if not cls._ARCHETYPES_CACHE:
            raise ValueError("Archetypes cache is empty")
        return random.choice(cls._ARCHETYPES_CACHE)

    @classmethod
    def get_teacher_profile(cls) -> TeacherProfileRecord:
        if cls._TEACHER_PROFILES_CACHE is None:
            rows = cls._fetch_all("SELECT subject, catchphrase FROM teacher_profiles")
            if not rows:
                raise ValueError("No teacher_profiles found in DB")
            cls._TEACHER_PROFILES_CACHE = [TeacherProfileRecord(subject=r[0], catchphrase=r[1]) for r in rows]
        if not cls._TEACHER_PROFILES_CACHE:
            raise ValueError("Teacher profiles cache is empty")
        return random.choice(cls._TEACHER_PROFILES_CACHE)

    @classmethod
    def get_family(cls) -> str:
        if cls._FAMILIES_CACHE is None:
            cls._FAMILIES_CACHE = [r[0] for r in cls._fetch_all("SELECT name FROM families")]
        if not cls._FAMILIES_CACHE:
            raise ValueError("No families found in DB")
        return random.choice(cls._FAMILIES_CACHE)

    @classmethod
    def get_quirk(cls) -> str:
        if cls._QUIRKS_CACHE is None:
            cls._QUIRKS_CACHE = [r[0] for r in cls._fetch_all("SELECT name FROM quirks")]
        if not cls._QUIRKS_CACHE:
            raise ValueError("No quirks found in DB")
        return random.choice(cls._QUIRKS_CACHE)

    @classmethod
    def get_flaw(cls) -> str:
        if cls._FLAWS_CACHE is None:
            cls._FLAWS_CACHE = [r[0] for r in cls._fetch_all("SELECT name FROM flaws")]
        if not cls._FLAWS_CACHE:
            raise ValueError("No flaws found in DB")
        return random.choice(cls._FLAWS_CACHE)

    @classproperty
    def ARCHETYPES(cls) -> list[ArchetypeRecord]:
        if cls._ARCHETYPES_CACHE is None:
            cls.get_archetype()
        if not cls._ARCHETYPES_CACHE:
            raise ValueError("Archetypes cache is empty")
        return cls._ARCHETYPES_CACHE

    @classproperty
    def TEACHER_PROFILES(cls) -> list[TeacherProfileRecord]:
        if cls._TEACHER_PROFILES_CACHE is None:
            cls.get_teacher_profile()
        if not cls._TEACHER_PROFILES_CACHE:
            raise ValueError("Teacher profiles cache is empty")
        return cls._TEACHER_PROFILES_CACHE

    @classproperty
    def FAMILIES(cls) -> list[str]:
        if cls._FAMILIES_CACHE is None:
            cls.get_family()
        if not cls._FAMILIES_CACHE:
            raise ValueError("Families cache is empty")
        return cls._FAMILIES_CACHE

    @classproperty
    def QUIRKS(cls) -> list[str]:
        if cls._QUIRKS_CACHE is None:
            cls.get_quirk()
        if not cls._QUIRKS_CACHE:
            raise ValueError("Quirks cache is empty")
        return cls._QUIRKS_CACHE

    @classproperty
    def FLAWS(cls) -> list[str]:
        if cls._FLAWS_CACHE is None:
            cls.get_flaw()
        if not cls._FLAWS_CACHE:
            raise ValueError("Flaws cache is empty")
        return cls._FLAWS_CACHE
