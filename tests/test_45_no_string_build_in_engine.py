from __future__ import annotations

from pathlib import Path



def test_no_legacy_string_builder_in_being_engine(repo_root: Path) -> None:
    content = (repo_root / "novel_engine/core/being_engine.py").read_text(encoding="utf-8")
    assert "def get_student_detail(" not in content
    assert "def get_mc_report(" not in content
    assert " | 技能:" not in content
