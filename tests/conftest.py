from collections.abc import Iterator
import pytest
import app as othello
from flask.testing import FlaskClient
from storage import GameStore

@pytest.fixture
def client(monkeypatch) -> Iterator[FlaskClient]:
    # Flaskをテストモードにする
    othello.app.config.update(TESTING=True)

    # テスト専用の空のストレージに差し替える
    monkeypatch.setattr(othello, "store", GameStore())

    # 前回の修正どおり、withで囲まず提供する
    yield othello.app.test_client()
