from __future__ import annotations

"""IO helpers used by engine runtime."""

import os
import re
import sqlite3
from typing import Dict

from novel_engine.core.contracts import CurriculumWeek
from novel_engine.core.engine_constants import CURRICULUM_SUBJECT_INDEXES


def get_curriculum_from_db(db_path: str, abs_week: int) -> CurriculumWeek:
    """Load and normalize curriculum data for the requested absolute week."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Curriculum DB not found: {db_path}")

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM curriculum WHERE week = ?", (abs_week,))
        row = cursor.fetchone()

    if row is None:
        raise ValueError(f"No curriculum data for abs_week={abs_week}")

    subjects: Dict[str, str] = {}
    for subject, idx in CURRICULUM_SUBJECT_INDEXES.items():
        if idx >= len(row):
            raise ValueError(f"Malformed curriculum row: missing index {idx} for {subject}")
        subjects[subject] = re.sub(r"!\[.*?\]\(.*?\)", "", str(row[idx]))

    return CurriculumWeek(abs_week=abs_week, subjects=subjects)
