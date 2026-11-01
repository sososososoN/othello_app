from math import inf

from ai.evaluation import WEIGHTS, evaluate_board
from game import (
    BLACK,
    WHITE,
    Board,
    Position,
    get_flippable_stones,
    get_valid_moves,
)
from ai.models import SearchStats


def apply_move(
    board: Board,
    y: int,
    x: int,
    player: int,
) -> Board:
    """元の盤面を変更せず、着手後の新しい盤面を返す。"""
    new_board = [row.copy() for row in board]
    flippable = get_flippable_stones(board, y, x, player)

    if not flippable:
        raise ValueError("Illegal move")

    new_board[y][x] = player

    for fy, fx in flippable:
        new_board[fy][fx] = player

    return new_board


def order_moves(
    board: Board,
    moves: list[Position],
    player: int,
) -> list[Position]:
    """位置評価値を基準に合法手を並べ替える。"""
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
    stats: SearchStats | None = None,
) -> int:
    """αβ枝刈りを用いて局面のMinimax評価値を返す。"""
    if stats is not None:
        stats.nodes_visited += 1

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

        return minimax(board, depth - 1, alpha, beta, opponent, stats=stats)

    if player == WHITE:
        best = -inf

        for y, x in moves:
            next_board = apply_move(board, y, x, player)
            value = minimax(next_board, depth - 1, alpha, beta, opponent, stats=stats)

            best = max(best, value)
            alpha = max(alpha, best)

            if alpha >= beta:
                if stats is not None:
                    stats.cutoffs += 1
                break

        return int(best)

    best = inf

    for y, x in moves:
        next_board = apply_move(board, y, x, player)
        value = minimax(next_board, depth - 1, alpha, beta, opponent, stats=stats)

        best = min(best, value)
        beta = min(beta, best)

        if alpha >= beta:
            if stats is not None:
                stats.cutoffs += 1
            break

    return int(best)
