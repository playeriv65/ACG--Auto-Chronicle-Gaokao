from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DB_PATH = Path("novel_engine/data/storage/world_data.db")
AGENT_EVENTS_PATH = Path("events_extraction/agent_events.jsonl")
LEGACY_CLEANED_PATH = Path("events_extraction/legacy_events_cleaned.jsonl")


def _legacy_event_to_template(description: str) -> str:
    text = description.strip()
    if text.startswith("【"):
        return text
    return f"【日常时段·校园】{{p1}}遭遇：{text}"


def _load_agent_templates(path: Path) -> list[str]:
    if not path.exists():
        return []
    templates: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        obj = json.loads(s)
        content = obj.get("content")
        if isinstance(content, str) and content:
            templates.append(content)
    return templates


def _load_legacy_cleaned_rows(path: Path) -> list[tuple[str, str, str]]:
    if not path.exists():
        return []
    rows: list[tuple[str, str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        obj = json.loads(s)
        if not isinstance(obj, dict):
            continue
        season = obj.get("season")
        content = obj.get("content")
        effect = obj.get("effect")
        if isinstance(season, str) and isinstance(content, str):
            rows.append((season, content, effect if isinstance(effect, str) else ""))
    return rows


def sync_event_pool() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"DB not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS event_pool (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                season TEXT NOT NULL DEFAULT 'ANY',
                template TEXT NOT NULL,
                effect TEXT NOT NULL DEFAULT '',
                enabled INTEGER NOT NULL DEFAULT 1,
                UNIQUE(source, template)
            )
            """
        )

        cursor.execute("DELETE FROM event_pool WHERE source IN ('legacy', 'agent')")

        legacy_cleaned_rows = _load_legacy_cleaned_rows(LEGACY_CLEANED_PATH)
        if legacy_cleaned_rows:
            legacy_inserts = [("legacy", season, content, effect, 1) for season, content, effect in legacy_cleaned_rows]
        else:
            cursor.execute("SELECT season, description, effect FROM events")
            legacy_rows = cursor.fetchall()
            legacy_inserts = [
                ("legacy", season, _legacy_event_to_template(description), effect or "", 1)
                for season, description, effect in legacy_rows
            ]
        if legacy_inserts:
            cursor.executemany(
                "INSERT INTO event_pool (source, season, template, effect, enabled) VALUES (?, ?, ?, ?, ?)",
                legacy_inserts,
            )

        agent_templates = _load_agent_templates(AGENT_EVENTS_PATH)
        agent_inserts = [("agent", "ANY", template, "", 1) for template in agent_templates]
        if agent_inserts:
            cursor.executemany(
                "INSERT INTO event_pool (source, season, template, effect, enabled) VALUES (?, ?, ?, ?, ?)",
                agent_inserts,
            )

        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM event_pool")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM event_pool WHERE source='legacy'")
        legacy_cnt = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM event_pool WHERE source='agent'")
        agent_cnt = cursor.fetchone()[0]
        mode = "ai_cleaned_legacy" if legacy_cleaned_rows else "raw_legacy_wrapped"
        print(f"event_pool synced: total={total}, legacy={legacy_cnt}, agent={agent_cnt}, legacy_mode={mode}")
    finally:
        conn.close()


if __name__ == "__main__":
    sync_event_pool()
