from math import inf

from backend.ai.evaluation import WEIGHTS, evaluate_board
from backend.game import (
    BLACK,
    WHITE,
    Board,
    Position,
    get_flippable_stones,
    get_valid_moves,
)
from backend.ai.models import SearchStats


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
    maximizing_player: int = WHITE,
) -> int:
    """αβ枝刈りを用いて局面のMinimax評価値を返す。"""
    if stats is not None:
        stats.nodes_visited += 1

    if player not in (BLACK, WHITE):
        raise ValueError("Invalid player")

    if maximizing_player not in (BLACK, WHITE):
        raise ValueError("Invalid maximizing player")

    if depth < 0:
        raise ValueError("Depth must be non-negative")

    if depth == 0:
        return evaluate_board(
            board,
            perspective=maximizing_player,
        )

    moves = order_moves(
        get_valid_moves(board, player),
        player,
    )

    opponent = 3 - player

    if not moves:
        opponent_moves = get_valid_moves(board, opponent)

        if not opponent_moves:
            return evaluate_board(
                board,
                perspective=maximizing_player,
            )

        return minimax(
            board,
            depth - 1,
            alpha,
            beta,
            opponent,
            stats=stats,
            maximizing_player=maximizing_player,
        )

    if player == maximizing_player:
        best = -inf

        for y, x in moves:
            next_board = apply_move(board, y, x, player)
            value = minimax(
                next_board,
                depth - 1,
                alpha,
                beta,
                opponent,
                stats=stats,
                maximizing_player=maximizing_player,
            )

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
        value = minimax(
            next_board,
            depth - 1,
            alpha,
            beta,
            opponent,
            stats=stats,
            maximizing_player=maximizing_player,
        )

        best = min(best, value)
        beta = min(beta, best)

        if alpha >= beta:
            if stats is not None:
                stats.cutoffs += 1
            break

    return int(best)
