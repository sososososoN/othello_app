import pytest
from game import BLACK, WHITE, Game, create_board


def test_initial_board() -> None:
    game = Game()
    assert game.turn == BLACK
    assert game.stone_counts() == (2, 2)
    assert len(game.board) == 8
    assert all(len(row) == 8 for row in game.board)


def test_initial_valid_moves() -> None:
    game = Game()
    assert set(game.valid_moves()) == {
        (2, 3),
        (3, 2),
        (4, 5),
        (5, 4),
    }


def test_place_and_flip() -> None:
    game = Game()
    result = game.place(2, 3)
    assert result is True
    assert game.board[2][3] == BLACK
    assert game.board[3][3] == BLACK

    assert game.turn == WHITE
    assert game.stone_counts() == (4, 1)


def test_invalid_move_does_not_change_board() -> None:
    game = Game()
    before = [row.copy() for row in game.board]
    result = game.place(0, 0)
    assert result is False
    assert game.board == before
    assert game.turn == BLACK


def test_result() -> None:
    game = Game()
    game.place(2, 3)
    game.reset()
    assert game.board == create_board()
    assert game.turn == BLACK
    assert game.message == ""


def test_games_are_independent() -> None:
    game1 = Game()
    game2 = Game()
    game1.place(2, 3)
    assert game1.board != game2.board
    assert game2.board == create_board()


def test_invalid_player_raises_error() -> None:
    from game import get_flippable_stones

    with pytest.raises(ValueError):
        get_flippable_stones(create_board(), 2, 3, 99)
