from collections.abc import Callable, Iterator
from contextlib import contextmanager
from copy import deepcopy
from game import EMPTY, WHITE, Board, Game, Position
from ai.engine import DIFFICULTY_DEPTH, choose_cpu_move
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
        self.cpu_selector = cpu_selector

    @contextmanager
    def _update(self) -> Iterator[None]:
        with self.record.lock:
            original_game = deepcopy(self.record.game)
            original_mode = self.record.mode
            original_difficulty = self.record.difficulty
            original_version = self.record.version
            try:
                yield
                self.record.persist()
            except Exception:
                self.record.game = original_game
                self.record.mode = original_mode
                self.record.difficulty = original_difficulty
                self.record.version = original_version
                raise

    def _snapshot_unlocked(self) -> dict:
        game = self.record.game
        return {
            "board": [row.copy() for row in game.board],
            "turn": game.turn,
            "message": game.message,
            "mode": self.record.mode,
            "difficulty": self.record.difficulty,
            "valid_moves": [[y, x] for y, x in game.valid_moves()],
        }

    def state(self) -> dict:
        with self.record.lock:
            return self._snapshot_unlocked()

    def change_mode(self, mode: str) -> dict:
        if mode not in ("pvp", "pvc"):
            raise GameError("Invalid game mode", 400)
        with self._update():
            if mode == self.record.mode:
                return self._snapshot_unlocked()
            game = self.record.game
            stone_count = sum(cell != EMPTY for row in game.board for cell in row)
            if stone_count > 4 or game.turn == EMPTY:
                raise GameError("Reset before changing mode", 409)
            self.record.mode = mode
            return self._snapshot_unlocked()

    def change_difficulty(self, difficulty: str) -> dict:
        if difficulty not in DIFFICULTY_DEPTH:
            raise GameError("Invalid difficulty", 400)

        with self._update():
            if self.record.mode != "pvc":
                raise GameError(
                    "Difficulty is available only in PvC mode",
                    409,
                )

            game = self.record.game

            stone_count = sum(cell != EMPTY for row in game.board for cell in row)

            if stone_count > 4 or game.turn == EMPTY:
                raise GameError(
                    "Reset before changing difficulty",
                    409,
                )

            self.record.difficulty = difficulty
            return self._snapshot_unlocked()

    def _play_human_turn(self, game: Game, y: int, x: int) -> None:
        if game.turn == EMPTY:
            raise GameError("Game has ended", 409)
        if self.record.mode == "pvc" and game.turn == WHITE:
            raise GameError("It is CPU's turn", 409)
        if not game.place(y, x):
            raise GameError("Illegal move", 400)

    def _play_cpu_turn(
        self,
        game: Game,
        selected_move: Position | None = None,
    ) -> None:
        if selected_move is not None:
            move = selected_move
        elif self.cpu_selector is not None:
            move = self.cpu_selector(game.board)
        else:
            depth = DIFFICULTY_DEPTH[self.record.difficulty]
            move = choose_cpu_move(game.board, depth=depth)
        if move is None:
            raise RuntimeError("CPU has no valid move")
        if not game.place(*move):
            raise RuntimeError("CPU selected an illegal move")

    def play(self, y: int, x: int) -> dict:
        with self._update():
            game = self.record.game
            self._play_human_turn(game, y, x)
            if self.record.mode == "pvc":
                while game.turn == WHITE:
                    self._play_cpu_turn(game)
            return self._snapshot_unlocked()

    def play_human(self, y: int, x: int) -> dict:
        with self._update():
            self._play_human_turn(self.record.game, y, x)
            return self._snapshot_unlocked()

    def play_cpu(
        self,
        preselected_move: Position | None = None,
    ) -> dict:
        with self._update():
            game = self.record.game

            if self.record.mode != "pvc":
                raise GameError("CPU move requires PvC mode", 409)

            if game.turn != WHITE:
                raise GameError("It is not CPU's turn", 409)

            self._play_cpu_turn(game, preselected_move)

            while game.turn == WHITE:
                self._play_cpu_turn(game)

            return self._snapshot_unlocked()

    def reset(self) -> dict:
        with self._update():
            self.record.game.reset()
            return self._snapshot_unlocked()
