from math import inf

from game import (
    BLACK,
    WHITE,
    EMPTY,
    DIRECTIONS,
    Board,
    Position,
    get_flippable_stones,
    get_valid_moves,
)
from ai.evaluation import WEIGHTS, WIN_SCORE, evaluate_board
from ai.search import apply_move, minimax, order_moves

DIFFICULTY_DEPTH: dict[str, int] = {
    "easy": 1,
    "normal": 3,
    "hard": 5,
}


def count_adjacent_empty_cells(
    board: Board,
    y: int,
    x: int,
) -> int:
    count = 0
    for dy, dx in DIRECTIONS:
        ny, nx = y + dy, x + dx
        if 0 <= ny < 8 and 0 <= nx < 8 and board[ny][nx] == EMPTY:
            count += 1
    return count


def choose_cpu_move(
    board: Board,
    depth: int | None = None,
) -> Position | None:
    moves = order_moves(
        board,
        get_valid_moves(board, WHITE),
        WHITE,
    )

    if not moves:
        return None

    stone_count = sum(cell != EMPTY for row in board for cell in row)

    if depth is None:
        depth = 5 if stone_count > 48 else 4

    if depth < 0:
        raise ValueError("Depth must be non-negative")

    best_move = moves[0]
    best_score = -inf

    for y, x in moves:
        flippable = get_flippable_stones(board, y, x, WHITE)

        penalty = sum(count_adjacent_empty_cells(board, fy, fx) for fy, fx in flippable)

        next_board = apply_move(board, y, x, WHITE)

        score = minimax(
            next_board,
            depth,
            -inf,
            inf,
            BLACK,
        )

        total_score = score - penalty * 2

        if total_score > best_score:
            best_score = total_score
            best_move = (y, x)

    return best_move
