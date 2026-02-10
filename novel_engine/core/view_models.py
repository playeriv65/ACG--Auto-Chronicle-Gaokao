from __future__ import annotations

from typing import List

from novel_engine.core.contracts import StrictModel


class StudentDetailDTO(StrictModel):
    name: str
    gender: str
    soul_desc: str
    last_week_rank: int
    total_mastery: int
    skills: List[str]


class MCReportDTO(StrictModel):
    rank: int
    skill: str
    stress: int
