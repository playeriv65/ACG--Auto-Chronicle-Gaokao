from __future__ import annotations

from novel_engine.core.view_models import BattleReportDTO, MCReportDTO, StudentDetailDTO


def render_student_detail(dto: StudentDetailDTO) -> str:
    rendered_gender = "男" if dto.is_male else "女"
    skills = " | ".join(dto.skills) if dto.skills else "无"
    return (
        f"{dto.name}({rendered_gender}) | {dto.soul_desc} | "
        f"排名:{dto.last_week_rank} | 修为:{dto.total_mastery} | 技能:{skills}"
    )


def render_mc_report(dto: MCReportDTO) -> str:
    rendered_skill = dto.latest_skill or "无"
    return f"排名:{dto.rank} | 技能:{rendered_skill} | 压力:{dto.stress}"


def render_battle_report(dto: BattleReportDTO) -> str:
    if dto.diff > 10:
        if dto.latest_skill is None:
            raise ValueError("Dominant victory report requires latest_skill")
        result = f"{dto.protagonist_name}使用了‘{dto.latest_skill}’，提前交卷，留下一个孤傲的背影。"
    elif dto.diff > -20:
        result = f"{dto.protagonist_name}与{dto.top_student_name}在分数线上反复拉锯，最终险胜/惜败。"
    else:
        result = f"{dto.protagonist_name}被压轴题镇压，道心破碎，看着{dto.top_student_name}绝尘而去。"

    return f"【战报】{dto.scene} {result} (我方战力:{dto.mc_score} vs 榜首:{dto.rival_score})"
