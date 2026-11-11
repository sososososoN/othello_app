from collections.abc import Iterator
from pathlib import Path

import pytest
import app as othello

from fastapi.testclient import TestClient
from storage import GameStore


@pytest.fixture
def client(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Iterator[TestClient]:
    frontend_dist = tmp_path / "frontend-dist"
    frontend_dist.mkdir()
    (frontend_dist / "index.html").write_text(
        "<!doctype html><html><head>"
        "<title>Othello AI Lab</title></head>"
        '<body><div id="root"></div></body></html>',
        encoding="utf-8",
    )
    monkeypatch.setattr(othello, "FRONTEND_DIST_DIR", frontend_dist)
    monkeypatch.setattr(othello, "store", GameStore())

    with TestClient(othello.app) as test_client:
        yield test_client
