from collections.abc import Callable, Iterator
from contextlib import contextmanager
from copy import deepcopy
from game import EMPTY, WHITE, Board, Position
from cpu import choose_cpu_move
from storage import GameRecord

CpuSelector = Callable[[Board], Position | None]


class GameError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
    ):
        super().__init__(message)
        self.status_code = status_code


class GameService:
    def __init__(
        self,
        record: GameRecord,
        cpu_selector: CpuSelector | None = None,
    ) -> None:
        self.record = record
        self.cpu_selector = (
            cpu_selector if cpu_selector is not None else choose_cpu_move
        )

    @contextmanager
    def _update(self) -> Iterator[None]:
        with self.record.lock:
            original_game = deepcopy(self.record.game)
            original_mode = self.record.mode
            try:
                yield
                self.record.persist()
            except Exception:
                self.record.game = original_game
                self.record.mode = original_mode
                raise

    def state(self) -> dict:
        with self.record.lock:
            game = self.record.game
            return {
                "board": [row.copy() for row in game.board],
                "turn": game.turn,
                "message": game.message,
                "mode": self.record.mode,
                "valid_moves": [[y, x] for y, x in game.valid_moves()],
            }

    def change_mode(self, mode: str) -> None:
        if mode not in ("pvp", "pvc"):
            raise GameError("Invalid game mode", 400)
        with self._update():
            if mode == self.record.mode:
                return
            game = self.record.game
            stone_count = sum(cell != EMPTY for row in game.board for cell in row)
            if stone_count > 4 or game.turn == EMPTY:
                raise GameError("Reset before changing mode", 409)
            self.record.mode = mode

    def play(self, y: int, x: int) -> None:
        with self._update():
            game = self.record.game
            if game.turn == EMPTY:
                raise GameError("Game has ended", 409)
            if self.record.mode == "pvc" and game.turn == WHITE:
                raise GameError("It is CPU's turn", 409)
            if not game.place(y, x):
                raise GameError("Illegal move", 400)
            if self.record.mode == "pvc":
                while game.turn == WHITE:
                    move = self.cpu_selector(game.board)
                    if move is None:
                        raise RuntimeError("CPU has no valid move")
                    if not game.place(*move):
                        raise RuntimeError("CPU selected an illegal move")

    def reset(self) -> None:
        with self._update():
            self.record.game.reset()
