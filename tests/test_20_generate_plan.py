from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from helpers import assert_json_shape, run_cmd
from novel_engine.core.contracts import WeeklyScript, WorldSettings


def test_generate_plan_in_isolated_workspace(isolated_workspace: Path, repo_root: Path) -> None:
    load_dotenv(dotenv_path=repo_root / ".env", override=False)
    env = dict(os.environ)
    env["MODEL_NAME"] = env.get("TEST_MODEL_NAME", "glm-4.5-flash")
    if env.get("GLM_API_KEY"):
        env["API_KEY"] = env["GLM_API_KEY"]
    if env.get("GLM_BASE_URL"):
        env["BASE_URL"] = env["GLM_BASE_URL"]
    env.setdefault("BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")

    cmd = ["uv", "run", "python", "generate_full_plan.py"]
    res = run_cmd(cmd, cwd=isolated_workspace, timeout=300, env=env)
    assert res.returncode == 0, (
        "PLAN_GENERATION_FAILED\n"
        f"cmd={' '.join(cmd)}\n"
        f"stdout={res.stdout}\n"
        f"stderr={res.stderr}"
    )

    world_settings = assert_json_shape(isolated_workspace / "world_settings.json", ["meta", "characters"])
    assert isinstance(world_settings["characters"], list) and world_settings["characters"], "PLAN_GENERATION_FAILED: empty characters"
    validated_world = WorldSettings.model_validate(world_settings)
    first_character = validated_world.characters[0]
    assert first_character.role in {"protagonist", "classmate", "teacher"}
    assert isinstance(first_character.is_elite, bool)
    assert first_character.family and first_character.flaw and first_character.quirk
    assert "background" not in world_settings["characters"][0], "PLAN_GENERATION_FAILED: background must be removed"

    weekly_script = assert_json_shape(isolated_workspace / "weekly_script.json", ["meta", "weeks"])
    assert isinstance(weekly_script["weeks"], dict) and weekly_script["weeks"], "PLAN_GENERATION_FAILED: empty weeks"
    validated_weekly = WeeklyScript.model_validate(weekly_script)
    first_week = next(iter(validated_weekly.weeks.values()))
    assert "排名:" in first_week.rankings.mc_report, "PLAN_GENERATION_FAILED: mc_report should be rendered text"
