from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

from helpers import run_cmd



def test_run_one_chapter_in_isolated_workspace(isolated_workspace: Path, repo_root: Path) -> None:
    load_dotenv(dotenv_path=repo_root / ".env", override=False)
    env = dict(os.environ)
    env["MODEL_NAME"] = env.get("TEST_MODEL_NAME", "glm-4.5-flash")
    if env.get("GLM_API_KEY"):
        env["API_KEY"] = env["GLM_API_KEY"]
    if env.get("GLM_BASE_URL"):
        env["BASE_URL"] = env["GLM_BASE_URL"]
    env.setdefault("BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")

    cmd = ["timeout", "240s", "uv", "run", "python", "main.py"]
    res = run_cmd(cmd, cwd=isolated_workspace, timeout=260, env=env)

    # main.py is loop-based; timeout 124 is acceptable if one chapter already landed.
    assert res.returncode in (0, 124), (
        "CHAPTER_GENERATION_FAILED(process_exit)\n"
        f"cmd={' '.join(cmd)}\n"
        f"stdout={res.stdout}\n"
        f"stderr={res.stderr}"
    )

    chapter_files = sorted((isolated_workspace / "novel_chapters").glob("Chapter_001_*.txt"))
    save_state = isolated_workspace / "save_state.json"

    chapter_ok = len(chapter_files) > 0
    save_ok = False
    if save_state.exists():
        state = json.loads(save_state.read_text(encoding="utf-8"))
        save_ok = int(state.get("chapter_count", 0)) >= 2

    assert chapter_ok or save_ok, (
        "CHAPTER_GENERATION_FAILED(output_validation)\n"
        f"chapter_files={[p.name for p in chapter_files]}\n"
        f"save_state_exists={save_state.exists()}\n"
        f"stdout={res.stdout}\n"
        f"stderr={res.stderr}"
    )
