import json
import sqlite3
from collections.abc import Callable, Iterator
from contextlib import contextmanager

from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock
from uuid import uuid4
from weakref import WeakValueDictionary

from backend.game import BLACK, Game


class ConcurrentUpdateError(RuntimeError):
    """同じ対局を複数のプロセスが同時に更新しようとした場合に発生する例外。"""


@dataclass
class GameRecord:
    game: Game = field(default_factory=Game)
    mode: str = "pvp"
    difficulty: str = "normal"
    human_color: int = BLACK
    started: bool = False
    version: int = 0
    lock: RLock = field(default_factory=RLock)
    save_callback: Callable[[], None] | None = field(
        default=None,
        repr=False,
        compare=False,
    )

    def persist(self) -> None:
        if self.save_callback is not None:
            self.save_callback()


class GameStore:
    def __init__(self) -> None:
        self._records: dict[str, GameRecord] = {}
        self._lock = RLock()

    def create(self) -> tuple[str, GameRecord]:
        with self._lock:
            game_id = uuid4().hex
            record = GameRecord()
            self._records[game_id] = record
            return game_id, record

    def get(self, game_id: str) -> GameRecord | None:
        with self._lock:
            return self._records.get(game_id)

    def delete(self, game_id: str) -> bool:
        with self._lock:
            if game_id not in self._records:
                return False
            del self._records[game_id]
            return True

    def count(self) -> int:
        with self._lock:
            return len(self._records)


class SQLiteGameStore:
    def __init__(self, db_path: str | Path) -> None:
        self._records: WeakValueDictionary[str, GameRecord] = WeakValueDictionary()
        self._lock = RLock()
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self._initialize()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(
            self.db_path,
            timeout=10,
        )
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS games(
                    game_id TEXT PRIMARY KEY,
                    board TEXT NOT NULL,
                    turn INTEGER NOT NULL,
                    mode TEXT NOT NULL,
                    message TEXT NOT NULL,
                    difficulty TEXT NOT NULL DEFAULT 'normal'
                        CHECK (difficulty IN ('easy', 'normal', 'hard')),
                    human_color INTEGER NOT NULL DEFAULT 1
                        CHECK (human_color IN (1, 2)),
                    started INTEGER NOT NULL DEFAULT 0
                        CHECK (started IN (0, 1)),
                    version INTEGER NOT NULL DEFAULT 0
                )
                """
            )

            columns = {
                row[1]
                for row in connection.execute("PRAGMA table_info(games)").fetchall()
            }

            if "difficulty" not in columns:
                connection.execute(
                    """
                    ALTER TABLE games
                    ADD COLUMN difficulty TEXT NOT NULL
                    DEFAULT 'normal'
                    CHECK (difficulty IN ('easy', 'normal', 'hard'))
                    """
                )

            if "version" not in columns:
                connection.execute(
                    """
                    ALTER TABLE games
                    ADD COLUMN version INTEGER NOT NULL DEFAULT 0
                    """
                )

            if "human_color" not in columns:
                connection.execute(
                    """
                    ALTER TABLE games
                    ADD COLUMN human_color INTEGER NOT NULL DEFAULT 1
                    CHECK (human_color IN (1, 2))
                    """
                )

            if "started" not in columns:
                connection.execute(
                    """
                    ALTER TABLE games
                    ADD COLUMN started INTEGER NOT NULL DEFAULT 0
                    CHECK (started IN (0, 1))
                    """
                )

            from backend.game import create_board

            rows = connection.execute(
                "SELECT game_id, board, turn FROM games"
            ).fetchall()
            for game_id, board_json, turn in rows:
                board = json.loads(board_json)
                if board != create_board() or turn == 0:
                    connection.execute(
                        "UPDATE games SET started = 1 WHERE game_id = ?",
                        (game_id,),
                    )

    def _bind(self, game_id: str, record: GameRecord) -> None:
        record.save_callback = lambda: self._save(
            game_id,
            record,
        )

    def _save(self, game_id: str, record: GameRecord) -> None:
        with self._lock:
            with self._connection() as connection:
                cursor = connection.execute(
                    """
                    UPDATE games 
                    SET
                        board = ?,
                        turn = ?,
                        mode = ?,
                        message = ?,
                        difficulty = ?,
                        human_color = ?,
                        started = ?,
                        version = version + 1
                    WHERE game_id = ? AND version = ?
                    """,
                    (*self._record_values(record), game_id, record.version),
                )
                if cursor.rowcount != 1:
                    exists = connection.execute(
                        "SELECT 1 FROM games WHERE game_id = ?",
                        (game_id,),
                    ).fetchone()
                    if self._records.get(game_id) is record:
                        self._records.pop(game_id, None)
                    if exists is None:
                        raise LookupError(f"Game not found {game_id}")
                    raise ConcurrentUpdateError(
                        f"Game was updated concurrently: {game_id}"
                    )
            record.version += 1

    def _insert(self, game_id: str, record: GameRecord) -> None:
        with self._lock:
            with self._connection() as connection:
                connection.execute(
                    """
                    INSERT INTO games (
                        game_id, board, turn, mode, message, difficulty, human_color, started
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (game_id, *self._record_values(record)),
                )

    def create(self) -> tuple[str, GameRecord]:
        with self._lock:
            game_id = uuid4().hex
            record = GameRecord()
            self._insert(game_id, record)
            self._bind(game_id, record)
            self._records[game_id] = record
            return game_id, record

    def get(self, game_id: str) -> GameRecord | None:
        with self._lock:
            cached = self._records.get(game_id)
            with self._connection() as connection:
                row = connection.execute(
                    """
                    SELECT board, turn, mode, message, difficulty, human_color, started, version
                    FROM games
                    WHERE game_id = ?
                    """,
                    (game_id,),
                ).fetchone()
            if row is None:
                self._records.pop(game_id, None)
                return None
            board, turn, mode, message, difficulty, human_color, started, version = row
            if cached is not None and cached.version == version:
                return cached
            record = GameRecord(
                game=Game(
                    board=json.loads(board),
                    turn=turn,
                    message=message,
                ),
                mode=mode,
                difficulty=difficulty,
                human_color=human_color,
                started=bool(started),
                version=version,
            )
            self._bind(game_id, record)
            self._records[game_id] = record
            return record

    def delete(self, game_id: str) -> bool:
        with self._lock:
            with self._connection() as connection:
                cursor = connection.execute(
                    "DELETE FROM games WHERE game_id = ?",
                    (game_id,),
                )

            self._records.pop(game_id, None)
            return cursor.rowcount > 0

    def count(self) -> int:
        with self._lock:
            with self._connection() as connection:
                row = connection.execute("SELECT COUNT(*) FROM games").fetchone()
            return row[0]

    @staticmethod
    def _record_values(
        record: GameRecord,
    ) -> tuple[str, int, str, str, str, int, int]:
        game = record.game
        return (
            json.dumps(game.board),
            game.turn,
            record.mode,
            game.message,
            record.difficulty,
            record.human_color,
            int(record.started),
        )
