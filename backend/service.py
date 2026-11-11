from collections.abc import Callable, Iterator
from contextlib import contextmanager
from copy import deepcopy
from secrets import choice

from backend.game import BLACK, EMPTY, WHITE, Board, Game, Position
from backend.ai.engine import DIFFICULTY_DEPTH, choose_cpu_move
from backend.storage import GameRecord

CpuSelector = Callable[[Board], Position | None]


class GameError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
    ) -> None:
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

    @property
    def cpu_color(self) -> int:
        return 3 - self.record.human_color

    @contextmanager
    def _update(self) -> Iterator[None]:
        with self.record.lock:
            original_game = deepcopy(self.record.game)
            original_mode = self.record.mode
            original_difficulty = self.record.difficulty
            original_human_color = self.record.human_color
            original_started = self.record.started
            original_version = self.record.version
            try:
                yield
                self.record.persist()
            except Exception:
                self.record.game = original_game
                self.record.mode = original_mode
                self.record.difficulty = original_difficulty
                self.record.human_color = original_human_color
                self.record.started = original_started
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
            "human_color": self.record.human_color,
            "started": self.record.started,
            "cpu_color": (self.cpu_color if self.record.mode == "pvc" else None),
            "valid_moves": [[y, x] for y, x in game.valid_moves()],
        }

    def state(self) -> dict:
        with self.record.lock:
            return self._snapshot_unlocked()

    def start_game(
        self,
        mode: str,
        difficulty: str = "normal",
        human_order: str = "first",
    ) -> dict:
        if mode not in ("pvp", "pvc"):
            raise GameError("Invalid game mode", 400)
        if difficulty not in DIFFICULTY_DEPTH:
            raise GameError("Invalid difficulty", 400)
        if human_order not in ("first", "second", "random"):
            raise GameError("Invalid human order", 400)
        if mode == "pvp" and human_order != "first":
            raise GameError(
                "Human order requires PvC mode",
                400,
            )
        if mode == "pvc" and human_order == "random":
            human_color = choice((BLACK, WHITE))
        elif human_order == "second":
            human_color = WHITE
        else:
            human_color = BLACK

        with self._update():
            if self.record.started:
                raise GameError("Reset before starting a new game", 409)
            self.record.game.reset()
            self.record.mode = mode
            self.record.difficulty = difficulty
            self.record.human_color = human_color
            self.record.started = True

            if mode == "pvc" and human_color == WHITE:
                self._play_cpu_until_human_turn()
            return self._snapshot_unlocked()

    def change_mode(self, mode: str) -> dict:
        if mode not in ("pvp", "pvc"):
            raise GameError("Invalid game mode", 400)

        with self._update():
            if mode == self.record.mode:
                return self._snapshot_unlocked()

            if self.record.started:
                raise GameError("Reset before changing settings", 409)

            self.record.mode = mode
            self.record.human_color = BLACK
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

            if self.record.started:
                raise GameError("Reset before changing settings", 409)

            self.record.difficulty = difficulty
            return self._snapshot_unlocked()

    def _play_human_turn(self, game: Game, y: int, x: int) -> None:
        if game.turn == EMPTY:
            raise GameError("Game has ended", 409)
        if self.record.mode == "pvc" and game.turn != self.record.human_color:
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

            if self.cpu_color == WHITE:
                move = choose_cpu_move(
                    game.board,
                    depth=depth,
                )
            else:
                move = choose_cpu_move(
                    game.board,
                    depth=depth,
                    player=BLACK,
                )
        if move is None:
            raise RuntimeError("CPU has no valid move")
        if not game.place(*move):
            raise RuntimeError("CPU selected an illegal move")

    def _play_cpu_until_human_turn(
        self,
        selected_move: Position | None = None,
    ) -> None:
        game = self.record.game
        while game.turn == self.cpu_color:
            self._play_cpu_turn(game, selected_move)
            selected_move = None

    def play(self, y: int, x: int) -> dict:
        with self._update():
            game = self.record.game
            self._play_human_turn(game, y, x)
            self.record.started = True
            if self.record.mode == "pvc":
                self._play_cpu_until_human_turn()
            return self._snapshot_unlocked()

    def play_human(self, y: int, x: int) -> dict:
        with self._update():
            self._play_human_turn(self.record.game, y, x)
            self.record.started = True
            return self._snapshot_unlocked()

    def play_cpu(
        self,
        preselected_move: Position | None = None,
    ) -> dict:
        with self._update():
            game = self.record.game

            if self.record.mode != "pvc":
                raise GameError("CPU move requires PvC mode", 409)

            if game.turn != self.cpu_color:
                raise GameError("It is not CPU's turn", 409)

            self._play_cpu_until_human_turn(preselected_move)
            return self._snapshot_unlocked()

    def reset(self) -> dict:
        with self._update():
            self.record.game.reset()
            self.record.human_color = BLACK
            self.record.started = False
            return self._snapshot_unlocked()
