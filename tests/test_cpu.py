from math import inf

import pytest

from game import BLACK, WHITE, Game, create_board, get_valid_moves
from cpu import (
    WEIGHTS,
    WIN_SCORE,
    apply_move,
    choose_cpu_move,
    evaluate_board,
    minimax,
    order_moves,
)


def test_apply_move() -> None:
    board = create_board()
    next_board = apply_move(board, 2, 4, WHITE)

    assert next_board[2][4] == WHITE
    assert next_board[3][4] == WHITE
    assert board == create_board()


def test_invalid_move() -> None:
    with pytest.raises(ValueError):
        apply_move(create_board(), 0, 0, WHITE)


def test_choose_cpu_move() -> None:
    game = Game()
    assert game.place(2, 3)

    original_board = [row.copy() for row in game.board]

    move = choose_cpu_move(game.board, depth=2)

    assert move in game.valid_moves()
    assert game.board == original_board


def test_cpu_no_valid_moves() -> None:
    board = [[BLACK] * 8 for _ in range(8)]
    assert choose_cpu_move(board, depth=2) is None


def test_terminal_evaluation() -> None:
    board = [[WHITE] * 8 for _ in range(8)]
    assert evaluate_board(board) > WIN_SCORE


def test_minimax_pass() -> None:
    board = [[BLACK] * 8 for _ in range(8)]
    board[0][0] = 0
    board[0][1] = WHITE

    score = minimax(
        board,
        depth=2,
        alpha=-inf,
        beta=inf,
        player=WHITE,
    )

    assert score < -WIN_SCORE


def test_order_moves_prioritizes_high_weight_cells() -> None:
    board = create_board()
    moves = [(1, 1), (0, 0), (2, 2)]

    ordered = order_moves(board, moves, WHITE)

    assert ordered[0] == (0, 0)
    assert ordered[-1] == (1, 1)


def test_order_moves_does_not_mutate_input() -> None:
    board = create_board()
    moves = [(2, 3), (3, 2), (4, 5)]
    original = moves.copy()

    order_moves(board, moves, WHITE)

    assert moves == original


def test_order_moves_preserves_moves() -> None:
    board = create_board()
    moves = get_valid_moves(board, BLACK)

    ordered = order_moves(board, moves, BLACK)

    assert sorted(ordered) == sorted(moves)


def test_position_weights_favor_corners() -> None:
    assert WEIGHTS[0][0] > WEIGHTS[1][1]
    assert WEIGHTS[7][7] > WEIGHTS[6][6]


def test_initial_board_is_balanced() -> None:
    assert evaluate_board(create_board()) == 0


def test_terminal_white_win_has_high_score() -> None:
    board = [[WHITE] * 8 for _ in range(8)]

    assert evaluate_board(board) > WIN_SCORE


def test_terminal_black_win_has_low_score() -> None:
    board = [[BLACK] * 8 for _ in range(8)]

    assert evaluate_board(board) < -WIN_SCORE


def test_cpu_returns_legal_move() -> None:
    game = Game()
    assert game.place(2, 3)

    move = choose_cpu_move(game.board, depth=1)

    assert move in game.valid_moves()


def test_cpu_does_not_change_original_board() -> None:
    game = Game()
    assert game.place(2, 3)

    original = [row.copy() for row in game.board]

    choose_cpu_move(game.board, depth=1)

    assert game.board == original


def test_minimax_returns_integer() -> None:
    board = create_board()

    score = minimax(
        board,
        depth=2,
        alpha=-inf,
        beta=inf,
        player=WHITE,
    )

    assert isinstance(score, int)


def test_apply_move_does_not_mutate_original() -> None:
    board = create_board()
    original = [row.copy() for row in board]

    next_board = apply_move(board, 2, 4, WHITE)

    assert board == original
    assert next_board != board
