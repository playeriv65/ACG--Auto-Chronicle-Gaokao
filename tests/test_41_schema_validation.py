from __future__ import annotations

import pytest

from novel_engine.core.contracts import RuntimeState, WeeklyScript, WorldSettings



def test_world_settings_rejects_string_tags() -> None:
    payload = {
        "meta": {
            "title": "x",
            "generated_at": "2026-01-01 00:00:00",
            "description": "x",
            "system_prompt": {
                "role": "x",
                "style": "x",
                "background": "x",
                "requirements": "x",
            },
        },
        "characters": [
            {
                "name": "叶凌天",
                "gender": "男",
                "background": "[普通工薪, 拖延症, 喜欢转笔]",
                "tags": "['做题家']",
            }
        ],
    }

    with pytest.raises(Exception):
        WorldSettings.model_validate(payload)



def test_weekly_script_rejects_invalid_week_key() -> None:
    payload = {
        "meta": {"title": "x"},
        "weeks": {
            "week-1": {
                "event": "e",
                "date": "d",
                "details": ["d1"],
                "quiz": None,
                "rankings": {"mc_report": "m", "top_student": "t"},
            }
        },
    }

    with pytest.raises(Exception):
        WeeklyScript.model_validate(payload)



def test_runtime_state_rejects_missing_engine_state() -> None:
    payload = {
        "total_chars": 1,
        "chapter_count": 1,
        "year": 1,
        "semester": 1,
        "week": 1,
    }

    with pytest.raises(Exception):
        RuntimeState.model_validate(payload)
