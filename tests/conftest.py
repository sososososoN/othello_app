import pytest
import app as othello
from flask.testing import FlaskClient
from collections.abc import Iterator

@pytest.fixture
def client() -> Iterator[FlaskClient]:
    # Flaskをテスト用に設定
    othello.app.config.update(TESTING=True)
    # 他のテストで生成されたゲームを削除
    with othello.registry_lock:
        othello.games.clear()
    try:
        yield othello.app.test_client()
    finally:
        with othello.registry_lock:
            othello.games.clear()