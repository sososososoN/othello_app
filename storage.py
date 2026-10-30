import json
import sqlite3
from collections.abc import Callable, Iterator
from contextlib import contextmanager

from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock
from uuid import uuid4

from game import Game


@dataclass
class GameRecord:
    game: Game = field(default_factory=Game)
    mode: str = "pvp"
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


class SQLiteGameStore(GameStore):
    def __init__(self, db_path: str | Path) -> None:
        super().__init__()
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
                    message TEXT NOT NULL
                )
                """
            )

    def _bind(self, game_id: str, record: GameRecord) -> None:
        record.save_callback = lambda: self._save(
            game_id,
            record,
        )

    def _save(self, game_id: str, record: GameRecord) -> None:
        game = record.game
        with self._lock:
            with self._connection() as connection:
                connection.execute(
                    """
                    INSERT INTO games (
                        game_id,
                        board,
                        turn,
                        mode,
                        message
                    )
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT (game_id)
                    DO UPDATE SET
                        board = excluded.board,
                        turn = excluded.turn,
                        mode = excluded.mode,
                        message = excluded.message
                    """,
                    (
                        game_id,
                        json.dumps(game.board),
                        game.turn,
                        record.mode,
                        game.message,
                    ),
                )

    def create(self) -> tuple[str, GameRecord]:
        with self._lock:
            game_id, record = super().create()
            self._bind(game_id, record)
            try:
                record.persist()
            except Exception:
                super().delete(game_id)
                raise
            return game_id, record

    def get(self, game_id: str) -> GameRecord | None:
        with self._lock:
            cached = super().get(game_id)
            if cached is not None:
                return cached
            with self._connection() as connection:
                row = connection.execute(
                    """
                    SELECT board, turn, mode, message
                    FROM games
                    WHERE game_id = ?
                    """,
                    (game_id,),
                ).fetchone()
            if row is None:
                return None
            board, turn, mode, message = row
            record = GameRecord(
                game=Game(
                    board=json.loads(board),
                    turn=turn,
                    message=message,
                ),
                mode=mode,
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
            if cursor.rowcount == 0:
                return False
            self._records.pop(game_id, None)
            return True

    def count(self) -> int:
        with self._lock:
            with self._connection() as connection:
                row = connection.execute("SELECT COUNT(*) FROM games").fetchone()
            return row[0]
