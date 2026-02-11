from __future__ import annotations

from typing import List

from novel_engine.core.contracts import StrictModel


class StudentDetailDTO(StrictModel):
    name: str
    is_male: bool
    soul_desc: str
    last_week_rank: int
    total_mastery: int
    skills: List[str]


class MCReportDTO(StrictModel):
    rank: int
    latest_skill: str | None
    stress: int


class BattleReportDTO(StrictModel):
    scene: str
    protagonist_name: str
    top_student_name: str
    mc_score: int
    rival_score: int
    diff: int
    latest_skill: str | None
