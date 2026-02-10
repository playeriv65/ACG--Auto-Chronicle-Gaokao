from __future__ import annotations

"""Domain constants shared by core simulation modules."""

from typing import Dict

from novel_engine.data.database import Subject

# Weekly battle scoring subjects.
CORE_SUBJECTS = [Subject.MATH, Subject.PHYS, Subject.CHEM, Subject.BIO, Subject.ENG, Subject.CHN]

# Semantic markers used in logs and state.
ALL_SUBJECTS_MARKER = "全科"
INFO_TRACK_TAG = "信奥党"
TEACHER_ROLE = "老师"
CLASSMATE_ROLE = "同学"
PROTAGONIST_ROLE = "主角"
SUMMER_SEASON = "SUMMER"
WINTER_SEASON = "WINTER"

# Column indexes for curriculum rows read from sqlite.
CURRICULUM_SUBJECT_INDEXES: Dict[str, int] = {
    Subject.CHN: 1,
    Subject.MATH: 2,
    Subject.ENG: 3,
    Subject.PHYS: 4,
    Subject.CHEM: 5,
    Subject.BIO: 6,
    Subject.HIST: 7,
    Subject.GEO: 8,
    Subject.POLI: 9,
}
