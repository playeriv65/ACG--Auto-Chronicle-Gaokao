from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from helpers import run_cmd

_API_CHECK_SCRIPT = r"""
import sys
from openai import OpenAI

model_name = sys.argv[1]
base_url = sys.argv[2]
api_key = sys.argv[3]
if not base_url:
    raise RuntimeError("BASE_URL is empty")
if not api_key:
    raise RuntimeError("API_KEY is empty")

client = OpenAI(base_url=base_url, api_key=api_key)
completion = client.chat.completions.create(
    model=model_name,
    messages=[{"role": "user", "content": "请只回复：OK"}],
    temperature=0.3,
    top_p=0.9,
    max_tokens=32,
    stream=False,
)
choices = getattr(completion, "choices", None)
if not choices:
    raise RuntimeError("no choices in response")

print("API_OK")
"""


@pytest.mark.timeout(180)
def test_api_key_connectivity(repo_root: Path) -> None:
    load_dotenv(dotenv_path=repo_root / ".env", override=False)
    env = dict(os.environ)

    base_url = env.get("BASE_URL", "")
    api_key = env.get("API_KEY", "")
    model_name = env.get("MODEL_NAME", "")

    if not api_key:
        pytest.fail("API_KEY not set in .env")
    if not base_url:
        pytest.fail("BASE_URL not set in .env")
    if not model_name:
        pytest.fail("MODEL_NAME not set in .env")

    cmd = [
        "uv",
        "run",
        "python",
        "-c",
        _API_CHECK_SCRIPT,
        model_name,
        base_url,
        api_key,
    ]
    result = run_cmd(cmd, cwd=repo_root, timeout=60, env=env)

    if result.returncode != 0:
        pytest.fail(
            f"API_CONNECTIVITY_ERROR\n"
            f"returncode={result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    if "API_OK" not in result.stdout:
        pytest.fail(
            f"API_RESPONSE_ERROR\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
