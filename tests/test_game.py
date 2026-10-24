
import app as othello


def test_create_board():
    board = othello.create_board()

    assert len(board) == 8
    assert all(len(row) == 8 for row in board)
    assert sum(row.count(1) for row in board) == 2
    assert sum(row.count(2) for row in board) == 2
    assert sum(row.count(0) for row in board) == 60


def test_initial_valid_moves():
    board = othello.create_board()
    moves = othello.get_valid_moves(board, 1)

    assert {tuple(move) for move in moves} == {
        (2, 3), (3, 2), (4, 5), (5, 4)
    }


def test_flippable_stones():
    board = othello.create_board()
    result = othello.get_flippable_stones(board, 2, 3, 1)
    assert result == [(3, 3)]


def test_multiple_stones_flip():
    board = [[0] * 8 for _ in range(8)]
    board[3][3] = 2
    board[3][4] = 2
    board[3][5] = 1

    result = othello.get_flippable_stones(board, 3, 2, 1)
    assert result == [(3, 3), (3, 4)]


def test_invalid_move():
    board = othello.create_board()

    assert othello.get_flippable_stones(board, 0, 0, 1) == []
    assert othello.get_flippable_stones(board, 8, 8, 1) == []


def test_place_and_flip():
    othello.current_game = {
        "board": othello.create_board(),
        "turn": 1,
        "mode": "pvp",
        "message": "",
    }

    result = othello.place_and_flip(2, 3)

    assert result is True
    assert othello.current_game["board"][2][3] == 1
    assert othello.current_game["board"][3][3] == 1
    assert othello.current_game["turn"] == 2
