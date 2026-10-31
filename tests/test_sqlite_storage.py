import sqlite3

import pytest

from game import BLACK, WHITE
from service import GameService
from storage import SQLiteGameStore


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "othello.db"


@pytest.fixture
def store(db_path):
    return SQLiteGameStore(db_path)


def test_database_created(db_path):
    SQLiteGameStore(db_path)

    assert db_path.exists()

    with sqlite3.connect(db_path) as connection:
        tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()

    assert ("games",) in tables


def test_create_game(store):
    game_id, record = store.create()

    assert len(game_id) == 32
    assert record.game.turn == BLACK
    assert record.mode == "pvp"
    assert store.count() == 1


def test_restore_game_after_store_restart(db_path):
    store1 = SQLiteGameStore(db_path)
    game_id, record = store1.create()

    service = GameService(record)
    service.play(2, 3)

    store2 = SQLiteGameStore(db_path)
    restored = store2.get(game_id)

    assert restored is not None
    assert restored.game.board[2][3] == BLACK
    assert restored.game.board[3][3] == BLACK
    assert restored.game.turn == WHITE


def test_mode_persistence(db_path):
    store1 = SQLiteGameStore(db_path)
    game_id, record = store1.create()

    GameService(record).change_mode("pvc")

    store2 = SQLiteGameStore(db_path)
    restored = store2.get(game_id)

    assert restored is not None
    assert restored.mode == "pvc"


def test_reset_persistence(db_path):
    store1 = SQLiteGameStore(db_path)
    game_id, record = store1.create()

    service = GameService(record)
    service.play(2, 3)
    service.reset()

    store2 = SQLiteGameStore(db_path)
    restored = store2.get(game_id)

    assert restored is not None
    assert restored.game.turn == BLACK
    assert restored.game.board[2][3] == 0
    assert restored.game.stone_counts() == (2, 2)


def test_games_are_independent(db_path):
    store1 = SQLiteGameStore(db_path)

    id1, record1 = store1.create()
    id2, record2 = store1.create()

    GameService(record1).play(2, 3)

    store2 = SQLiteGameStore(db_path)
    restored1 = store2.get(id1)
    restored2 = store2.get(id2)

    assert restored1 is not None
    assert restored2 is not None

    assert restored1.game.board[2][3] == BLACK
    assert restored2.game.board[2][3] == 0


def test_delete_game(db_path):
    store1 = SQLiteGameStore(db_path)
    game_id, _ = store1.create()

    assert store1.delete(game_id) is True
    assert store1.delete(game_id) is False

    store2 = SQLiteGameStore(db_path)
    assert store2.get(game_id) is None
    assert store2.count() == 0


def test_nonexistent_game(store):
    assert store.get("unknown-id") is None


def test_invalid_move_does_not_change_database(db_path):
    store1 = SQLiteGameStore(db_path)
    game_id, record = store1.create()

    service = GameService(record)

    with pytest.raises(Exception):
        service.play(0, 0)

    store2 = SQLiteGameStore(db_path)
    restored = store2.get(game_id)

    assert restored is not None
    assert restored.game.stone_counts() == (2, 2)
    assert restored.game.turn == BLACK


def test_save_failure_rolls_back_memory(db_path, monkeypatch):
    store = SQLiteGameStore(db_path)
    game_id, record = store.create()
    service = GameService(record)

    original_save = store._save

    def failing_save(game_id, record):
        raise sqlite3.OperationalError("Simulated failure")

    monkeypatch.setattr(store, "_save", failing_save)

    with pytest.raises(sqlite3.OperationalError):
        service.play(2, 3)

    assert record.game.stone_counts() == (2, 2)
    assert record.game.turn == BLACK

    monkeypatch.setattr(store, "_save", original_save)

    restarted = SQLiteGameStore(db_path)
    restored = restarted.get(game_id)

    assert restored is not None
    assert restored.game.stone_counts() == (2, 2)


def test_difficulty_persistence(db_path) -> None:
    store1 = SQLiteGameStore(db_path)
    game_id, record = store1.create()

    service = GameService(record)
    service.change_mode("pvc")
    service.change_difficulty("hard")

    store2 = SQLiteGameStore(db_path)
    restored = store2.get(game_id)

    assert restored is not None
    assert restored.difficulty == "hard"


def test_existing_database_migrates_without_data_loss(
    db_path,
) -> None:
    # 旧スキーマのDBを準備
    store = SQLiteGameStore(db_path)
    game_id, _ = store.create()

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE games_old AS
            SELECT game_id, board, turn, mode, message
            FROM games
            """
        )
        connection.execute("DROP TABLE games")
        connection.execute(
            """
            ALTER TABLE games_old RENAME TO games
            """
        )

    restarted = SQLiteGameStore(db_path)
    restored = restarted.get(game_id)

    assert restored is not None
    assert restored.difficulty == "normal"
    assert restarted.count() == 1
