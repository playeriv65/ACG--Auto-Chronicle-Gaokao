from __future__ import annotations

"""IO helpers used by engine runtime."""

import os
import re
import sqlite3
from typing import Dict, Optional

from novel_engine.core.engine_constants import CURRICULUM_SUBJECT_INDEXES


def get_curriculum_from_db(db_path: str, abs_week: int) -> Optional[Dict[str, str]]:
    """Load and normalize curriculum data for the requested absolute week."""
    if not os.path.exists(db_path):
        return None

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM curriculum WHERE week = ?", (abs_week,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None
        return _parse_curriculum_row(row)
    except Exception:
        return None


def _parse_curriculum_row(row: tuple) -> Dict[str, str]:
    """Map DB row columns to subject names and strip markdown image tags."""
    result = {subject: row[idx] for subject, idx in CURRICULUM_SUBJECT_INDEXES.items()}
    for subject, value in result.items():
        result[subject] = re.sub(r"!\[.*?\]\(.*?\)", "", str(value))
    return result
