from __future__ import annotations

from pathlib import Path

import pytest

from helpers import prepare_isolated_workspace


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def isolated_workspace(tmp_path_factory: pytest.TempPathFactory, repo_root: Path) -> Path:
    base = tmp_path_factory.mktemp("acg_fullchain")
    return prepare_isolated_workspace(base, repo_root)
