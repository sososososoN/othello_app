
import pytest

from pydantic import ValidationError

from game import Game
from schemas import GameStateResponse, MoveRequest


def valid_state() -> dict:
    game = Game()

    return {
        "board": game.board,
        "turn": game.turn,
        "message": game.message,
        "mode": "pvp",
        "valid_moves": [
            [y, x] for y, x in game.valid_moves()
        ],
    }


def test_valid_game_state() -> None:
    state = GameStateResponse.model_validate(valid_state())

    assert state.turn == 1
    assert state.mode == "pvp"
    assert len(state.board) == 8


def test_invalid_board_rows() -> None:
    data = valid_state()
    data["board"] = data["board"][:7]

    with pytest.raises(ValidationError):
        GameStateResponse.model_validate(data)


def test_invalid_board_columns() -> None:
    data = valid_state()
    data["board"][0] = data["board"][0][:7]

    with pytest.raises(ValidationError):
        GameStateResponse.model_validate(data)


def test_invalid_cell_value() -> None:
    data = valid_state()
    data["board"][0][0] = 9

    with pytest.raises(ValidationError):
        GameStateResponse.model_validate(data)


def test_invalid_turn() -> None:
    data = valid_state()
    data["turn"] = 3

    with pytest.raises(ValidationError):
        GameStateResponse.model_validate(data)


def test_invalid_valid_move() -> None:
    data = valid_state()
    data["valid_moves"] = [[8, 3]]

    with pytest.raises(ValidationError):
        GameStateResponse.model_validate(data)


def test_valid_move_request() -> None:
    move = MoveRequest(
        y=2,
        x=3,
        mode="pvp",
    )

    assert move.y == 2
    assert move.x == 3


def test_invalid_move_request_type() -> None:
    with pytest.raises(ValidationError):
        MoveRequest(
            y="2",
            x=3,
            mode="pvp",
        )
