import pytest
import app as othello
from game import Game

@pytest.fixture
def client(monkeypatch):
    # Flaskをテスト用に設定
    othello.app.config.update(TESTING=True)

    # 各テストが独立したGameインスタンスを使う
    monkeypatch.setattr(othello, "current_game", Game())

    # モードも初期値に戻す
    monkeypatch.setattr(othello, "current_mode", "pvp")

    # 実際のサーバーを起動せずAPIをテスト
    with othello.app.test_client() as test_client:
        yield test_client