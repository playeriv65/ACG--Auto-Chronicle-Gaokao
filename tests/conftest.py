from __future__ import annotations

import sys
from pathlib import Path

import pytest

from helpers import prepare_isolated_workspace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def isolated_workspace(tmp_path_factory: pytest.TempPathFactory, repo_root: Path) -> Path:
    base = tmp_path_factory.mktemp("acg_fullchain")
    return prepare_isolated_workspace(base, repo_root)
