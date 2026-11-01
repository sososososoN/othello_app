import pytest

from ai.engine import (
    DIFFICULTY_DEPTH,
    choose_cpu_move,
    count_adjacent_empty_cells,
)
from game import BLACK, WHITE, Game, create_board, get_valid_moves


def test_difficulty_depths() -> None:
    """難易度と探索深さの対応が正しいことを確認する。"""
    assert DIFFICULTY_DEPTH == {
        "easy": 1,
        "normal": 3,
        "hard": 5,
    }


def test_cpu_returns_legal_move() -> None:
    """CPUが白の合法手を返すことを確認する。"""
    game = Game()
    assert game.place(2, 3)

    move = choose_cpu_move(game.board, depth=1)

    assert move is not None
    assert move in get_valid_moves(game.board, WHITE)


def test_cpu_does_not_mutate_board() -> None:
    """探索によって元の盤面が変更されないことを確認する。"""
    game = Game()
    assert game.place(2, 3)
    original = [row.copy() for row in game.board]

    choose_cpu_move(game.board, depth=1)

    assert game.board == original


def test_cpu_returns_none_when_no_moves() -> None:
    """白に合法手がない場合はNoneを返す。"""
    board = [[BLACK] * 8 for _ in range(8)]

    assert choose_cpu_move(board, depth=1) is None


def test_negative_depth_raises() -> None:
    """探索深さが負数の場合は例外を返す。"""
    board = create_board()

    with pytest.raises(ValueError, match="Depth must be non-negative"):
        choose_cpu_move(board, depth=-1)


def test_adjacent_empty_cells_on_initial_board() -> None:
    """初期盤面で隣接する空きマス数を確認する。"""
    board = create_board()

    assert count_adjacent_empty_cells(board, 3, 3) == 5


def test_cpu_returns_deterministic_move() -> None:
    """同じ盤面と探索深さなら同じ手を選択する。"""
    game = Game()
    assert game.place(2, 3)

    first = choose_cpu_move(game.board, depth=1)
    second = choose_cpu_move(game.board, depth=1)

    assert first is not None
    assert first == second


def test_cpu_does_not_select_occupied_cell() -> None:
    """CPUが既に石の置かれたマスを選ばないことを確認する。"""
    game = Game()
    assert game.place(2, 3)

    move = choose_cpu_move(game.board, depth=1)

    assert move is not None
    y, x = move
    assert game.board[y][x] != WHITE
    assert game.board[y][x] == 0
