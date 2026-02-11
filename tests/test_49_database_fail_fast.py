from __future__ import annotations

import sqlite3

import pytest

from novel_engine.data import database


def _create_empty_db(path: str) -> None:
    with sqlite3.connect(path) as conn:
        cur = conn.cursor()
        cur.execute("CREATE TABLE skills (subject TEXT, name TEXT, level INTEGER, description TEXT)")
        cur.execute("CREATE TABLE events (season TEXT, description TEXT, effect TEXT)")
        cur.execute("CREATE TABLE surnames (name TEXT, frequency INTEGER)")
        cur.execute("CREATE TABLE given_names (name TEXT, gender TEXT, era TEXT)")
        cur.execute("CREATE TABLE archetypes (name TEXT, title TEXT, base_stats TEXT)")
        cur.execute("CREATE TABLE teacher_profiles (subject TEXT, catchphrase TEXT)")
        cur.execute("CREATE TABLE families (name TEXT)")
        cur.execute("CREATE TABLE quirks (name TEXT)")
        cur.execute("CREATE TABLE flaws (name TEXT)")
        conn.commit()


def test_database_fail_fast_on_empty_sources(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    db_file = tmp_path / "empty_world.db"
    _create_empty_db(str(db_file))

    original_caches = (
        database.NPCData._SURNAMES_CACHE,
        database.NPCData._SURNAMES_WEIGHTS_CACHE,
        database.NPCData._ARCHETYPES_CACHE,
        database.NPCData._TEACHER_PROFILES_CACHE,
        database.NPCData._FAMILIES_CACHE,
        database.NPCData._QUIRKS_CACHE,
        database.NPCData._FLAWS_CACHE,
    )

    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    try:
        database.NPCData._SURNAMES_CACHE = None
        database.NPCData._SURNAMES_WEIGHTS_CACHE = None
        database.NPCData._ARCHETYPES_CACHE = None
        database.NPCData._TEACHER_PROFILES_CACHE = None
        database.NPCData._FAMILIES_CACHE = None
        database.NPCData._QUIRKS_CACHE = None
        database.NPCData._FLAWS_CACHE = None

        with pytest.raises(ValueError):
            database.SkillTree.get_skill_by_subject(database.Subject.MATH, 1000)

        with pytest.raises(ValueError):
            database.get_random_event("SUMMER")

        with pytest.raises(ValueError):
            database.NPCData.get_name("M", "00s")

        with pytest.raises(ValueError):
            database.NPCData.get_archetype()

        with pytest.raises(ValueError):
            database.NPCData.get_teacher_profile()

        with pytest.raises(ValueError):
            database.NPCData.get_family()
    finally:
        (
            database.NPCData._SURNAMES_CACHE,
            database.NPCData._SURNAMES_WEIGHTS_CACHE,
            database.NPCData._ARCHETYPES_CACHE,
            database.NPCData._TEACHER_PROFILES_CACHE,
            database.NPCData._FAMILIES_CACHE,
            database.NPCData._QUIRKS_CACHE,
            database.NPCData._FLAWS_CACHE,
        ) = original_caches
