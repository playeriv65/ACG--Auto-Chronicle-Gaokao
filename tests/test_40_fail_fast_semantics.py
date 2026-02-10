from __future__ import annotations

from pathlib import Path

import pytest

from novel_engine.core import ai_writer
from novel_engine.core.being_engine import BeingEngine
from novel_engine.core.contracts import WorldSettings
from novel_engine.core.engine_io import get_curriculum_from_db
from helpers import prepare_isolated_workspace, run_cmd



def test_main_fails_on_bad_world_settings(tmp_path: Path, repo_root: Path) -> None:
    workdir = prepare_isolated_workspace(tmp_path, repo_root)
    (workdir / "world_settings.json").write_text('{"meta": {}}', encoding="utf-8")

    cmd = ["uv", "run", "python", "main.py"]
    res = run_cmd(cmd, cwd=workdir, timeout=60)
    assert res.returncode != 0, "main.py should fail fast on invalid world_settings.json"



def test_engine_io_raises_on_missing_or_empty_curriculum() -> None:
    with pytest.raises(FileNotFoundError):
        get_curriculum_from_db("/tmp/definitely-not-exists.db", 1)

    with pytest.raises(ValueError):
        get_curriculum_from_db("novel_engine/data/storage/course_data.db", 99999)



def test_init_from_settings_rejects_non_json_tags() -> None:
    engine = BeingEngine()
    bad_settings = {
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
        ]
    }

    with pytest.raises(Exception):
        settings = WorldSettings.model_validate(bad_settings)
        engine.init_from_settings(settings)



def test_ai_writer_call_api_raises_without_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeCompletions:
        def __init__(self) -> None:
            self.calls = 0

        def create(self, *args, **kwargs):  # noqa: ANN002, ANN003
            self.calls += 1
            raise RuntimeError("boom")

    class FakeChat:
        def __init__(self) -> None:
            self.completions = FakeCompletions()

    class FakeClient:
        def __init__(self) -> None:
            self.chat = FakeChat()

    writer = ai_writer.AIWriter()
    fake_client = FakeClient()
    monkeypatch.setattr(writer, "client", fake_client)

    with pytest.raises(RuntimeError, match="boom"):
        writer._call_api([{"role": "user", "content": "x"}])

    assert fake_client.chat.completions.calls == 1
