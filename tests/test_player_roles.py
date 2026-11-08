import sqlite3

import pytest

import service as service_module
from game import BLACK, WHITE
from service import GameError, GameService
from storage import GameRecord, SQLiteGameStore


def test_human_first() -> None:
    """人間先攻なら、人間が黒・CPUが白になる。"""
    service = GameService(GameRecord())

    state = service.start_game(
        mode="pvc",
        difficulty="easy",
        human_order="first",
    )

    assert state["human_color"] == BLACK
    assert state["cpu_color"] == WHITE
    assert state["turn"] == BLACK

    # 初手はまだ人間が指していない
    assert sum(cell != 0 for row in state["board"] for cell in row) == 4


def test_cpu_first() -> None:
    """人間後攻ならCPUが黒で初手を指す。"""

    # 初期盤面で黒の合法手(2, 3)を選択させる
    service = GameService(
        GameRecord(),
        cpu_selector=lambda board: (2, 3),
    )

    state = service.start_game(
        mode="pvc",
        difficulty="easy",
        human_order="second",
    )

    assert state["human_color"] == WHITE
    assert state["cpu_color"] == BLACK
    assert state["board"][2][3] == BLACK
    assert state["turn"] == WHITE


def test_random_order_is_resolved_once(monkeypatch) -> None:
    """ランダムの結果は対局中に変わらない。"""
    calls = []

    def choose_white(colors):
        calls.append(colors)
        return WHITE

    monkeypatch.setattr(service_module, "choice", choose_white)

    service = GameService(
        GameRecord(),
        cpu_selector=lambda board: (2, 3),
    )

    state = service.start_game(
        mode="pvc",
        difficulty="easy",
        human_order="random",
    )

    assert state["human_color"] == WHITE
    assert state["cpu_color"] == BLACK
    assert len(calls) == 1

    # 状態を取得し直しても色が変わらない
    assert service.state()["human_color"] == WHITE
    assert len(calls) == 1


def test_human_cannot_play_on_cpu_turn() -> None:
    """CPUの番に人間が着手しようとすると409になる。"""
    service = GameService(
        GameRecord(mode="pvc", human_color=WHITE),
    )

    with pytest.raises(GameError) as exc_info:
        service.play_human(2, 3)

    assert exc_info.value.status_code == 409


def test_cpu_cannot_play_on_human_turn() -> None:
    """人間の番にCPUを実行しようとすると409になる。"""
    service = GameService(
        GameRecord(mode="pvc", human_color=BLACK),
    )

    with pytest.raises(GameError) as exc_info:
        service.play_cpu()

    assert exc_info.value.status_code == 409


def test_reset_restores_human_first() -> None:
    """リセット後は人間先攻の初期盤面に戻る。"""
    service = GameService(
        GameRecord(),
        cpu_selector=lambda board: (2, 3),
    )

    service.start_game(
        mode="pvc",
        difficulty="easy",
        human_order="second",
    )

    state = service.reset()

    assert state["human_color"] == BLACK
    assert state["cpu_color"] == WHITE
    assert state["turn"] == BLACK
    assert state["mode"] == "pvc"
    assert state["difficulty"] == "easy"

    assert sum(cell != 0 for row in state["board"] for cell in row) == 4


def test_sqlite_persists_human_color(tmp_path) -> None:
    """担当色がSQLiteに保存され、再読込できる。"""
    db_path = tmp_path / "roles.db"
    store = SQLiteGameStore(db_path)
    game_id, record = store.create()

    service = GameService(
        record,
        cpu_selector=lambda board: (2, 3),
    )

    service.start_game(
        mode="pvc",
        difficulty="easy",
        human_order="second",
    )

    # 別のストアを作り、DBから読み直す
    restored = SQLiteGameStore(db_path).get(game_id)

    assert restored is not None
    assert restored.human_color == WHITE
    assert restored.game.board[2][3] == BLACK
    assert restored.game.turn == WHITE


def test_migrates_existing_database(tmp_path) -> None:
    """旧スキーマのDBを削除せず、human_colorを追加する。"""
    db_path = tmp_path / "legacy.db"

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE games (
                game_id TEXT PRIMARY KEY,
                board TEXT NOT NULL,
                turn INTEGER NOT NULL,
                mode TEXT NOT NULL,
                message TEXT NOT NULL,
                difficulty TEXT NOT NULL DEFAULT 'normal',
                version INTEGER NOT NULL DEFAULT 0
            )
            """
        )

    # 初期化時にマイグレーションが実行される
    store = SQLiteGameStore(db_path)
    game_id, _ = store.create()
    restored = store.get(game_id)

    assert restored is not None
    assert restored.human_color == BLACK


def test_start_rolls_back_on_cpu_error() -> None:
    """CPU着手で失敗したら設定と盤面を元に戻す。"""
    service = GameService(
        GameRecord(),
        cpu_selector=lambda board: (0, 0),
    )
    before = service.state()

    with pytest.raises(
        RuntimeError,
        match="CPU selected an illegal move",
    ):
        service.start_game(
            mode="pvc",
            difficulty="hard",
            human_order="second",
        )

    assert service.state() == before


def test_invalid_human_order() -> None:
    """存在しない先後設定は拒否する。"""
    service = GameService(GameRecord())

    with pytest.raises(GameError) as exc_info:
        service.start_game(
            mode="pvc",
            human_order="unknown",
        )

    assert exc_info.value.status_code == 400
