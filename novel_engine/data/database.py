from __future__ import annotations

import json
import random
import sqlite3
from typing import Any, ClassVar, Sequence

from pydantic import BaseModel, ConfigDict

DB_PATH = "novel_engine/data/storage/world_data.db"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


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
    relation_delta: int
    mood_delta: int


class EventTemplateRecord(StrictModel):
    source: str
    season: str
    template: str
    effect: str
    relation_delta: int
    mood_delta: int


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
            cursor.execute(
                "SELECT name, level, description FROM skills WHERE subject = ? ORDER BY level",
                (subject,),
            )
            rows = cursor.fetchall()
            if not rows:
                raise ValueError(f"No skills found for subject: {subject}")

            skills = [
                SkillRecord(name=r[0], level=int(r[1]), description=r[2]) for r in rows
            ]
            idx = min(len(skills) - 1, max(0, int(mastery_val // 1000) - 1))
            unlocked = skills[: idx + 1]
            return random.choice(unlocked)
        finally:
            conn.close()


def get_random_event(
    season: str = "ANY", placeholders: dict[str, str] | None = None
) -> EventRecord:
    return get_random_event_from_pool(season=season, placeholders=placeholders)


def _render_event_template(template: str, placeholders: dict[str, str] | None) -> str:
    if placeholders is None:
        return template
    rendered = template
    for key, value in placeholders.items():
        rendered = rendered.replace(f"{{{key}}}", value)
        rendered = rendered.replace(f"{{{key.upper()}}}", value)
    return rendered


def _ensure_event_pool_schema(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS event_pool (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            season TEXT NOT NULL DEFAULT 'ANY',
            template TEXT NOT NULL,
            effect TEXT NOT NULL DEFAULT '',
            relation_delta INTEGER NOT NULL DEFAULT 0,
            mood_delta INTEGER NOT NULL DEFAULT 0,
            enabled INTEGER NOT NULL DEFAULT 1,
            UNIQUE(source, template)
        )
        """
    )
    cursor.execute("PRAGMA table_info(event_pool)")
    cols = {row[1] for row in cursor.fetchall()}
    if "relation_delta" not in cols:
        cursor.execute(
            "ALTER TABLE event_pool ADD COLUMN relation_delta INTEGER NOT NULL DEFAULT 0"
        )
    if "mood_delta" not in cols:
        cursor.execute(
            "ALTER TABLE event_pool ADD COLUMN mood_delta INTEGER NOT NULL DEFAULT 0"
        )


def _load_event_templates(
    cursor: sqlite3.Cursor, season: str
) -> list[EventTemplateRecord]:
    _ensure_event_pool_schema(cursor)
    cursor.execute(
        """
        SELECT source, season, template, effect, relation_delta, mood_delta
        FROM event_pool
        WHERE enabled = 1 AND (season = 'ANY' OR season = ?)
        """,
        (season,),
    )
    rows = cursor.fetchall()
    return [
        EventTemplateRecord(
            source=r[0],
            season=r[1],
            template=r[2],
            effect=r[3] or "",
            relation_delta=int(r[4]),
            mood_delta=int(r[5]),
        )
        for r in rows
    ]


def _table_exists(cursor: sqlite3.Cursor, table_name: str) -> bool:
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (table_name,)
    )
    return cursor.fetchone() is not None


def get_random_event_from_pool(
    season: str = "ANY", placeholders: dict[str, str] | None = None
) -> EventRecord:
    conn = DBConnector.get_connection()
    try:
        cursor = conn.cursor()

        if _table_exists(cursor, "event_pool"):
            templates = _load_event_templates(cursor, season)
            if templates:
                chosen = random.choice(templates)
                rendered = _render_event_template(chosen.template, placeholders)
                return EventRecord(
                    description=rendered,
                    effect=chosen.effect,
                    relation_delta=chosen.relation_delta,
                    mood_delta=chosen.mood_delta,
                )

        cursor.execute(
            "SELECT description, effect FROM events WHERE season = 'ANY' OR season = ?",
            (season,),
        )
        legacy_rows = cursor.fetchall()
        if not legacy_rows:
            raise ValueError(f"No events found for season: {season}")
        chosen = random.choice(legacy_rows)
        return EventRecord(
            description=chosen[0],
            effect=chosen[1] or "",
            relation_delta=0,
            mood_delta=0,
        )
    finally:
        conn.close()


class NPCData:
    _SURNAMES_CACHE: ClassVar[tuple[Sequence[str], Sequence[float]] | None] = None
    _SURNAMES_WEIGHTS_CACHE: ClassVar[tuple[Sequence[str], Sequence[float]] | None] = (
        None
    )
    _ARCHETYPES_CACHE: ClassVar[list[ArchetypeRecord] | None] = None
    _TEACHER_PROFILES_CACHE: ClassVar[list[TeacherProfileRecord] | None] = None
    _FAMILIES_CACHE: ClassVar[list[str] | None] = None
    _QUIRKS_CACHE: ClassVar[list[str] | None] = None
    _FLAWS_CACHE: ClassVar[list[str] | None] = None

    @classmethod
    def _get_surnames(cls) -> tuple[Sequence[str], Sequence[float]]:
        if cls._SURNAMES_CACHE is not None:
            return cls._SURNAMES_CACHE

        conn = DBConnector.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name, frequency FROM surnames")
            rows = cursor.fetchall()
            if not rows:
                raise ValueError("No surnames found in DB")
            surnames, weights = zip(*rows)
            cls._SURNAMES_CACHE = (surnames, weights)
            return cls._SURNAMES_CACHE
        finally:
            conn.close()

    @classmethod
    def _get_archetypes(cls) -> list[ArchetypeRecord]:
        if cls._ARCHETYPES_CACHE is not None:
            return cls._ARCHETYPES_CACHE

        conn = DBConnector.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name, title, base_stats FROM archetypes")
            rows = cursor.fetchall()
            if not rows:
                raise ValueError("No archetypes found in DB")
            archetypes = [
                ArchetypeRecord(name=r[0], title=r[1], base_stats=json.loads(r[2]))
                for r in rows
            ]
            cls._ARCHETYPES_CACHE = archetypes
            return cls._ARCHETYPES_CACHE
        finally:
            conn.close()

    @classmethod
    def _get_teacher_profiles(cls) -> list[TeacherProfileRecord]:
        if cls._TEACHER_PROFILES_CACHE is not None:
            return cls._TEACHER_PROFILES_CACHE

        conn = DBConnector.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT subject, catchphrase FROM teacher_profiles")
            rows = cursor.fetchall()
            if not rows:
                raise ValueError("No teacher_profiles found in DB")
            profiles = [
                TeacherProfileRecord(subject=r[0], catchphrase=r[1]) for r in rows
            ]
            cls._TEACHER_PROFILES_CACHE = profiles
            return cls._TEACHER_PROFILES_CACHE
        finally:
            conn.close()

    @classmethod
    def _get_families(cls) -> list[str]:
        if cls._FAMILIES_CACHE is not None:
            return cls._FAMILIES_CACHE

        conn = DBConnector.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM families")
            rows = cursor.fetchall()
            if not rows:
                raise ValueError("No families found in DB")
            families = [r[0] for r in rows]
            cls._FAMILIES_CACHE = families
            return cls._FAMILIES_CACHE
        finally:
            conn.close()

    @classmethod
    def _get_quirks(cls) -> list[str]:
        if cls._QUIRKS_CACHE is not None:
            return cls._QUIRKS_CACHE

        conn = DBConnector.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM quirks")
            rows = cursor.fetchall()
            if not rows:
                raise ValueError("No quirks found in DB")
            quirks = [r[0] for r in rows]
            cls._QUIRKS_CACHE = quirks
            return cls._QUIRKS_CACHE
        finally:
            conn.close()

    @classmethod
    def _get_flaws(cls) -> list[str]:
        if cls._FLAWS_CACHE is not None:
            return cls._FLAWS_CACHE

        conn = DBConnector.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM flaws")
            rows = cursor.fetchall()
            if not rows:
                raise ValueError("No flaws found in DB")
            flaws = [r[0] for r in rows]
            cls._FLAWS_CACHE = flaws
            return cls._FLAWS_CACHE
        finally:
            conn.close()

    @classmethod
    def _fetch_all(
        cls, query: str, params: Sequence[object] = ()
    ) -> list[tuple[Any, ...]]:
        conn = DBConnector.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            conn.close()

    @classmethod
    def get_name(cls, is_male: bool = True, era: str = "00s") -> str:
        surnames, weights = cls._get_surnames()
        surname = random.choices(surnames, weights=weights, k=1)[0]
        gender_code = "M" if is_male else "F"

        conn = DBConnector.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM given_names WHERE gender = ? AND era = ? ORDER BY RANDOM() LIMIT 1",
                (gender_code, era),
            )
            res = cursor.fetchone()
            if not res:
                raise ValueError(
                    f"No given_names found for gender={gender_code} era={era}"
                )
            return surname + res[0]
        finally:
            conn.close()

    @classmethod
    def get_archetype(cls) -> ArchetypeRecord:
        archetypes = cls._get_archetypes()
        if not archetypes:
            raise ValueError("Archetypes cache is empty")
        return random.choice(archetypes)

    @classmethod
    def get_teacher_profile(cls) -> TeacherProfileRecord:
        profiles = cls._get_teacher_profiles()
        if not profiles:
            raise ValueError("Teacher profiles cache is empty")
        return random.choice(profiles)

    @classmethod
    def get_family(cls) -> str:
        families = cls._get_families()
        if not families:
            raise ValueError("Families cache is empty")
        return random.choice(families)

    @classmethod
    def get_quirk(cls) -> str:
        quirks = cls._get_quirks()
        if not quirks:
            raise ValueError("Quirks cache is empty")
        return random.choice(quirks)

    @classmethod
    def get_flaw(cls) -> str:
        flaws = cls._get_flaws()
        if not flaws:
            raise ValueError("Flaws cache is empty")
        return random.choice(flaws)

    @classproperty
    def ARCHETYPES(cls) -> list[ArchetypeRecord]:
        archetypes = cls._get_archetypes()
        if not archetypes:
            raise ValueError("Archetypes cache is empty")
        return archetypes

    @classproperty
    def TEACHER_PROFILES(cls) -> list[TeacherProfileRecord]:
        profiles = cls._get_teacher_profiles()
        if not profiles:
            raise ValueError("Teacher profiles cache is empty")
        return profiles

    @classproperty
    def FAMILIES(cls) -> list[str]:
        families = cls._get_families()
        if not families:
            raise ValueError("Families cache is empty")
        return families

    @classproperty
    def QUIRKS(cls) -> list[str]:
        quirks = cls._get_quirks()
        if not quirks:
            raise ValueError("Quirks cache is empty")
        return quirks

    @classproperty
    def FLAWS(cls) -> list[str]:
        flaws = cls._get_flaws()
        if not flaws:
            raise ValueError("Flaws cache is empty")
        return flaws
