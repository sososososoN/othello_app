from collections.abc import Iterator

import pytest
import app as othello

from fastapi.testclient import TestClient
from storage import GameStore


@pytest.fixture
def client(monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setattr(othello, "store", GameStore())

    with TestClient(othello.app) as test_client:
        yield test_client
