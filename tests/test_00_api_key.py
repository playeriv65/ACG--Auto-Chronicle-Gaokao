from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from helpers import run_cmd

_API_CHECK_SCRIPT = r'''
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
'''


@pytest.mark.timeout(180)
def test_api_key_connectivity(repo_root: Path) -> None:
    providers = [
        ("nvidia", "z-ai/glm4.7", "NVIDIA_BASE_URL", "NVIDIA_API_KEY", "https://integrate.api.nvidia.com/v1"),
        ("glm", "glm-4.5-flash", "GLM_BASE_URL", "GLM_API_KEY", "https://open.bigmodel.cn/api/paas/v4/"),
    ]
    load_dotenv(dotenv_path=repo_root / ".env", override=False)
    env = dict(os.environ)
    failures: list[str] = []

    for provider, model_name, base_url_env, api_key_env, default_base_url in providers:
        base_url = env.get(base_url_env) or env.get("BASE_URL", default_base_url)
        api_key = env.get(api_key_env) or env.get("API_KEY", "")

        if not api_key:
            failures.append(f"provider={provider} missing key env: {api_key_env}")
            continue
        if not base_url:
            failures.append(f"provider={provider} missing base url env: {base_url_env}")
            continue

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
        try:
            result = run_cmd(cmd, cwd=repo_root, timeout=60, env=env)
        except Exception as exc:
            failures.append(f"provider={provider} error={exc}")
            continue

        if result.returncode != 0:
            failures.append(
                f"provider={provider} returncode={result.returncode}\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
            continue

        if "API_OK" not in result.stdout:
            failures.append(
                f"provider={provider} success marker missing\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )

    if failures:
        pytest.fail("API_AUTH_OR_PROVIDER_ERROR\n" + "\n\n".join(failures))
