import pytest
from math import inf

from game import BLACK, WHITE, Game, create_board
from cpu import (
    WIN_SCORE,
    apply_move,
    choose_cpu_move,
    evaluate_board,
    minimax,
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
