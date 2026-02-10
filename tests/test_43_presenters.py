from __future__ import annotations

from novel_engine.core.presenters import render_mc_report, render_student_detail
from novel_engine.core.view_models import MCReportDTO, StudentDetailDTO



def test_render_student_detail_stable() -> None:
    dto = StudentDetailDTO(
        name="叶凌天",
        gender="男",
        soul_desc="[普通工薪, 拖延症, 喜欢转笔]",
        last_week_rank=3,
        total_mastery=12345,
        skills=["洛必达法则", "构造法"],
    )
    text = render_student_detail(dto)
    assert "叶凌天(男)" in text
    assert "排名:3" in text
    assert "修为:12345" in text
    assert "洛必达法则 | 构造法" in text



def test_render_mc_report_stable() -> None:
    dto = MCReportDTO(rank=5, skill="构造法", stress=12)
    text = render_mc_report(dto)
    assert text == "排名:5 | 技能:构造法 | 压力:12"
