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


DIFFICULTY_DEPTH: dict[str, int] = {
    "easy": 1,
    "normal": 3,
    "hard": 5,
}


def apply_move(
    board: Board,
    y: int,
    x: int,
    player: int,
) -> Board:
    new_board = [row.copy() for row in board]
    flippable = get_flippable_stones(board, y, x, player)
    if not flippable:
        raise ValueError("Illegal move")
    new_board[y][x] = player
    for fy, fx in flippable:
        new_board[fy][fx] = player
    return new_board


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


def order_moves(
    board: Board,
    moves: list[Position],
    player: int,
) -> list[Position]:
    if player not in (BLACK, WHITE):
        raise ValueError("Invalid player")
    return sorted(
        moves,
        key=lambda move: WEIGHTS[move[0]][move[1]],
        reverse=True,
    )


def minimax(
    board: Board,
    depth: int,
    alpha: float,
    beta: float,
    player: int,
) -> int:
    if player not in (BLACK, WHITE):
        raise ValueError("Invalid player")
    if depth < 0:
        raise ValueError("Depth must be non-negative")
    if depth == 0:
        return evaluate_board(board)
    moves = order_moves(
        board,
        get_valid_moves(board, player),
        player,
    )
    opponent = 3 - player
    if not moves:
        opponent_moves = get_valid_moves(board, opponent)
        if not opponent_moves:
            return evaluate_board(board)
        return minimax(board, depth - 1, alpha, beta, opponent)
    if player == WHITE:
        best = -inf
        for y, x in moves:
            next_board = apply_move(board, y, x, player)
            value = minimax(
                next_board,
                depth - 1,
                alpha,
                beta,
                opponent,
            )
            best = max(best, value)
            alpha = max(alpha, best)
            if alpha >= beta:
                break
        return int(best)
    best = inf
    for y, x in moves:
        next_board = apply_move(board, y, x, player)
        value = minimax(
            next_board,
            depth - 1,
            alpha,
            beta,
            opponent,
        )
        best = min(best, value)
        beta = min(beta, best)
        if alpha >= beta:
            break
    return int(best)


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
