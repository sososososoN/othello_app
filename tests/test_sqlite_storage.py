import sqlite3

import pytest

import gc
import weakref
from weakref import WeakValueDictionary

from game import BLACK, WHITE
from service import GameService
from storage import SQLiteGameStore, GameRecord, ConcurrentUpdateError


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


def test_sqlite_store_is_independent_of_memory_store(db_path) -> None:
    """SQLiteストアがメモリストアを継承していないことを確認する。"""
    from storage import GameStore

    store = SQLiteGameStore(db_path)

    assert not isinstance(store, GameStore)


def test_create_persists_before_cache_registration(
    db_path,
    monkeypatch,
) -> None:
    """SQLite保存が失敗した対局はキャッシュに残さない。"""
    store = SQLiteGameStore(db_path)

    def failing_insert(game_id: str, record: GameRecord) -> None:
        raise sqlite3.OperationalError("Simulated failure")

    monkeypatch.setattr(store, "_insert", failing_insert)

    with pytest.raises(sqlite3.OperationalError):
        store.create()

    assert store._records == {}
    assert store.count() == 0


def test_sqlite_store_reuses_cached_record(db_path) -> None:
    """同じ対局IDでは既存のレコードを再利用する。"""
    store = SQLiteGameStore(db_path)

    game_id, record = store.create()

    assert store.get(game_id) is record
    assert store.get(game_id) is record


def test_delete_clears_cached_record(db_path) -> None:
    """SQLiteから削除した対局はキャッシュからも消える。"""
    store = SQLiteGameStore(db_path)

    game_id, _ = store.create()

    assert store.delete(game_id) is True
    assert store.get(game_id) is None
    assert game_id not in store._records


def test_deleted_game_cannot_be_resurrected(db_path) -> None:
    """削除済み対局を保存しても復活しない。"""
    store = SQLiteGameStore(db_path)
    game_id, record = store.create()

    # データベースから対局を削除
    assert store.delete(game_id) is True

    # 古いGameRecord参照から保存を試みる
    with pytest.raises(LookupError, match="Game not found"):
        record.persist()

    # 保存を試みた後も削除状態が維持される
    assert store.get(game_id) is None
    assert store.count() == 0


def test_existing_game_can_still_be_updated(db_path) -> None:
    """既存の対局はUPDATEによって正常に保存される。"""
    store = SQLiteGameStore(db_path)
    game_id, record = store.create()

    # GameServiceの既存の永続化処理を利用
    service = GameService(record)
    service.play(2, 3)

    # 別のストアインスタンスからDBを読み直す
    restored = SQLiteGameStore(db_path).get(game_id)

    assert restored is not None
    assert restored.game.board[2][3] == BLACK
    assert restored.game.turn == WHITE


def test_deleted_game_service_update_is_rolled_back(db_path) -> None:
    """削除済み対局への操作は失敗し、メモリ状態も復元される。"""
    store = SQLiteGameStore(db_path)
    game_id, record = store.create()
    service = GameService(record)

    before = service.state()
    assert store.delete(game_id) is True

    # メモリ上の着手に成功しても、DB保存に失敗する
    with pytest.raises(LookupError, match="Game not found"):
        service.play(2, 3)

    # GameService._update() がロールバックする
    assert service.state() == before
    assert store.count() == 0


def test_version_increments_after_update(db_path) -> None:
    """保存に成功するたびにバージョンが増加する。"""
    store = SQLiteGameStore(db_path)
    game_id, record = store.create()

    assert record.version == 0

    GameService(record).play(2, 3)

    assert record.version == 1

    restored = SQLiteGameStore(db_path).get(game_id)
    assert restored is not None
    assert restored.version == 1


def test_stale_update_is_rejected(db_path) -> None:
    """異なるストアの古いレコードで上書きできない。"""
    store_a = SQLiteGameStore(db_path)
    game_id, record_a = store_a.create()

    # 別プロセスを模して、別のストアで同じ対局を取得
    store_b = SQLiteGameStore(db_path)
    record_b = store_b.get(game_id)
    assert record_b is not None

    # Aが先に着手して保存
    GameService(record_a).play(2, 3)

    # Bは古いversion=0を保持している
    before = GameService(record_b).state()

    # Bの更新は競合として拒否される
    with pytest.raises(ConcurrentUpdateError):
        GameService(record_b).play(3, 2)

    # Bのメモリ状態は元に戻る
    assert GameService(record_b).state() == before

    # DBにはAの着手が残る
    current = SQLiteGameStore(db_path).get(game_id)
    assert current is not None
    assert current.game.board[2][3] == BLACK
    assert current.version == 1


def test_version_migration_preserves_games(db_path) -> None:
    """version列を持たない既存DBを移行できる。"""
    store = SQLiteGameStore(db_path)
    game_id, _ = store.create()

    # 古いスキーマを再現
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE games_old AS
            SELECT game_id, board, turn, mode, message, difficulty
            FROM games
            """
        )
        connection.execute("DROP TABLE games")
        connection.execute("ALTER TABLE games_old RENAME TO games")

    # 起動時にversion列が自動追加される
    migrated = SQLiteGameStore(db_path)
    restored = migrated.get(game_id)

    assert restored is not None
    assert restored.version == 0
    assert migrated.count() == 1


def test_conflict_evicts_stale_cached_record(db_path) -> None:
    """競合発生後はDBから最新のレコードを取得する。"""
    store_a = SQLiteGameStore(db_path)
    game_id, record_a = store_a.create()

    store_b = SQLiteGameStore(db_path)
    record_b = store_b.get(game_id)
    assert record_b is not None

    # 別ストアが先に更新
    GameService(record_b).play(2, 3)

    # Aの古い状態で更新すると競合する
    with pytest.raises(ConcurrentUpdateError):
        GameService(record_a).play(3, 2)

    # 古いレコードはキャッシュから除去された
    assert game_id not in store_a._records

    # 次のget()はDBから最新状態を読み込む
    refreshed = store_a.get(game_id)

    assert refreshed is not None
    assert refreshed is not record_a
    assert refreshed.game.board[2][3] == BLACK
    assert refreshed.version == 1


def test_sqlite_cache_uses_weak_references(db_path) -> None:
    """SQLiteストアが弱参照キャッシュを使うことを確認する。"""
    store = SQLiteGameStore(db_path)

    assert isinstance(store._records, WeakValueDictionary)


def test_unused_record_can_be_collected(db_path) -> None:
    """使用されなくなったレコードはキャッシュから消える。"""
    store = SQLiteGameStore(db_path)
    game_id, record = store.create()

    # 弱参照を作成する。これ自体は寿命を延ばさない
    reference = weakref.ref(record)

    # 通常の強参照を削除する
    del record

    # ガベージコレクションを明示的に実行
    gc.collect()

    assert reference() is None
    assert game_id not in store._records

    # メモリから消えてもSQLiteには残っている
    restored = store.get(game_id)
    assert restored is not None
    assert store.count() == 1


def test_active_record_keeps_same_identity(db_path) -> None:
    """使用中のレコードは同じインスタンスを返す。"""
    store = SQLiteGameStore(db_path)
    game_id, record = store.create()

    # 強参照があるので、GCしても生存する
    gc.collect()

    assert store.get(game_id) is record

    # 操作結果も同じレコードに反映される
    GameService(record).play(2, 3)

    assert store.get(game_id) is record
    assert record.version == 1
