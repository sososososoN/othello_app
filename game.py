from dataclasses import dataclass, field

BOARD_SIZE = 8
EMPTY = 0
BLACK = 1
WHITE = 2

DIRECTIONS = (
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
)

Board = list[list[int]]
Position = tuple[int, int]


def create_board() -> Board:
    board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    board[3][3] = WHITE
    board[3][4] = BLACK
    board[4][3] = BLACK
    board[4][4] = WHITE
    return board


def get_flippable_stones(
    board: Board,
    y: int,
    x: int,
    player: int,
) -> list[Position]:
    if player not in (BLACK, WHITE):
        raise ValueError("Invalid player")
    if not (0 <= y < BOARD_SIZE and 0 <= x < BOARD_SIZE):
        return []
    if board[y][x] != EMPTY:
        return []
    opponent = 3 - player
    flippable: list[Position] = []
    for dy, dx in DIRECTIONS:
        candidates: list[Position] = []
        cy, cx = y + dy, x + dx
        while (
            0 <= cy < BOARD_SIZE and 0 <= cx < BOARD_SIZE and board[cy][cx] == opponent
        ):
            candidates.append((cy, cx))
            cy += dy
            cx += dx
        if (
            candidates
            and 0 <= cy < BOARD_SIZE
            and 0 <= cx < BOARD_SIZE
            and board[cy][cx] == player
        ):
            flippable.extend(candidates)
    return flippable


def get_valid_moves(board: Board, player: int) -> list[Position]:
    return [
        (y, x)
        for y in range(BOARD_SIZE)
        for x in range(BOARD_SIZE)
        if get_flippable_stones(board, y, x, player)
    ]


@dataclass
class Game:
    board: Board = field(default_factory=create_board)
    turn: int = BLACK
    message: str = ""

    def valid_moves(self) -> list[Position]:
        if self.turn == EMPTY:
            return []
        return get_valid_moves(self.board, self.turn)

    def stone_counts(self) -> tuple[int, int]:
        black = sum(row.count(BLACK) for row in self.board)
        white = sum(row.count(WHITE) for row in self.board)
        return black, white

    def place(self, y: int, x: int) -> bool:
        if self.turn == EMPTY:
            return False

        player = self.turn
        flippable = get_flippable_stones(self.board, y, x, player)

        if not flippable:
            return False

        self.board[y][x] = player

        for fy, fx in flippable:
            self.board[fy][fx] = player

        opponent = 3 - player

        if get_valid_moves(self.board, opponent):
            self.turn = opponent
            self.message = ""
        elif get_valid_moves(self.board, player):
            self.turn = player
            self.message = "相手はパスです"
        else:
            self.turn = EMPTY
            black, white = self.stone_counts()
            self.message = f"終了！黒:{black} 白:{white}"

        return True

    def reset(self) -> None:
        self.board = create_board()
        self.turn = BLACK
        self.message = ""
