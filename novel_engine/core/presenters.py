from __future__ import annotations

from novel_engine.core.view_models import MCReportDTO, StudentDetailDTO


def render_student_detail(dto: StudentDetailDTO) -> str:
    skills = " | ".join(dto.skills) if dto.skills else "无"
    return (
        f"{dto.name}({dto.gender}) | {dto.soul_desc} | "
        f"排名:{dto.last_week_rank} | 修为:{dto.total_mastery} | 技能:{skills}"
    )


def render_mc_report(dto: MCReportDTO) -> str:
    rendered_skill = dto.latest_skill or "无"
    return f"排名:{dto.rank} | 技能:{rendered_skill} | 压力:{dto.stress}"
