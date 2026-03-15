from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

from helpers import run_cmd
from novel_engine.core.contracts import RuntimeState


def test_run_one_chapter_in_isolated_workspace(
    isolated_workspace: Path, repo_root: Path
) -> None:
    load_dotenv(dotenv_path=repo_root / ".env", override=False)
    env = dict(os.environ)

    if (
        not (isolated_workspace / "world_settings.json").exists()
        or not (isolated_workspace / "weekly_script.json").exists()
    ):
        # Use --active flag to target the active virtual environment
        prep_cmd = ["uv", "run", "--active", "python", "generate_full_plan.py"]
        prep_res = run_cmd(prep_cmd, cwd=isolated_workspace, timeout=300, env=env)
        assert prep_res.returncode == 0, (
            "CHAPTER_GENERATION_FAILED(prep_plan)\n"
            f"cmd={' '.join(prep_cmd)}\n"
            f"stdout={prep_res.stdout}\n"
            f"stderr={prep_res.stderr}"
        )

    # Use --active flag to target the active virtual environment
    cmd = ["timeout", "240s", "uv", "run", "--active", "python", "main.py"]
    res = run_cmd(cmd, cwd=isolated_workspace, timeout=260, env=env)

    assert res.returncode in (0, 124), (
        "CHAPTER_GENERATION_FAILED(process_exit)\n"
        f"cmd={' '.join(cmd)}\n"
        f"stdout={res.stdout}\n"
        f"stderr={res.stderr}"
    )

    chapter_files = sorted(
        (isolated_workspace / "novel_chapters").glob("Chapter_001_*.txt")
    )
    save_state = isolated_workspace / "save_state.json"

    chapter_ok = len(chapter_files) > 0
    save_ok = False
    if save_state.exists():
        state = json.loads(save_state.read_text(encoding="utf-8"))
        validated_state = RuntimeState.model_validate(state)
        save_ok = validated_state.chapter_count >= 2
        if validated_state.engine_state.students:
            assert all(
                skill.name for skill in validated_state.engine_state.students[0].skills
            )

    assert chapter_ok or save_ok, (
        "CHAPTER_GENERATION_FAILED(output_validation)\n"
        f"chapter_files={[p.name for p in chapter_files]}\n"
        f"save_state_exists={save_state.exists()}\n"
        f"stdout={res.stdout}\n"
        f"stderr={res.stderr}"
    )
