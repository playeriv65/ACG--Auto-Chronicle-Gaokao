from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Iterable, Sequence


def run_cmd(
    cmd: Sequence[str],
    cwd: Path,
    timeout: int,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    # Unset VIRTUAL_ENV to avoid uv warnings about path mismatch in isolated workspaces
    if env is not None and "VIRTUAL_ENV" in env:
        env = env.copy()
        del env["VIRTUAL_ENV"]
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def assert_json_shape(path: Path, required_keys: Iterable[str]) -> dict:
    assert path.exists(), f"expected file missing: {path}"
    data = json.loads(path.read_text(encoding="utf-8"))
    for key in required_keys:
        assert key in data, f"missing key '{key}' in {path}"
    return data


def prepare_isolated_workspace(tmp_path: Path, repo_root: Path) -> Path:
    workdir = tmp_path / "run_env"
    workdir.mkdir(parents=True, exist_ok=True)

    # Minimal runtime surface for full-chain tests.
    copy_targets = [
        "generate_full_plan.py",
        "main.py",
        "config.py",
        "pyproject.toml",
        "uv.lock",
        "text_for_gen",
        "novel_engine",
    ]

    for rel in copy_targets:
        src = repo_root / rel
        dst = workdir / rel
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    # Copy real credentials for online tests and mark as read-only.
    env_src = repo_root / ".env"
    if env_src.exists():
        env_dst = workdir / ".env"
        shutil.copy2(env_src, env_dst)
        env_dst.chmod(stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)

    # Keep output folder deterministic and isolated.
    (workdir / "novel_chapters").mkdir(parents=True, exist_ok=True)

    return workdir
