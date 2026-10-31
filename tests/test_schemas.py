import pytest
from pydantic import ValidationError

from game import Game
from schemas import DifficultyRequest, GameStateResponse, MoveRequest


def valid_state() -> dict:
    """正常なゲーム状態のテストデータを作成する。"""
    game = Game()

    return {
        "board": game.board,
        "turn": game.turn,
        "message": game.message,
        "mode": "pvp",
        "difficulty": "normal",
        "valid_moves": [[y, x] for y, x in game.valid_moves()],
    }


def test_valid_game_state() -> None:
    state = GameStateResponse.model_validate(valid_state())

    assert state.turn == 1
    assert state.mode == "pvp"
    assert state.difficulty == "normal"
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
    move = MoveRequest(y=2, x=3)

    assert move.y == 2
    assert move.x == 3


def test_invalid_move_request_type() -> None:
    with pytest.raises(ValidationError):
        MoveRequest(y="2", x=3)


@pytest.mark.parametrize(
    "difficulty",
    ["easy", "normal", "hard"],
)
def test_valid_difficulty_request(difficulty: str) -> None:
    request = DifficultyRequest(difficulty=difficulty)

    assert request.difficulty == difficulty


def test_invalid_difficulty_request() -> None:
    with pytest.raises(ValidationError):
        DifficultyRequest(difficulty="expert")


def test_missing_difficulty_request() -> None:
    with pytest.raises(ValidationError):
        DifficultyRequest.model_validate({})


@pytest.mark.parametrize(
    "difficulty",
    ["easy", "normal", "hard"],
)
def test_valid_difficulty_in_game_state(difficulty: str) -> None:
    data = valid_state()
    data["difficulty"] = difficulty

    state = GameStateResponse.model_validate(data)

    assert state.difficulty == difficulty


def test_invalid_difficulty_in_game_state() -> None:
    data = valid_state()
    data["difficulty"] = "expert"

    with pytest.raises(ValidationError):
        GameStateResponse.model_validate(data)


def test_missing_difficulty_in_game_state() -> None:
    data = valid_state()
    del data["difficulty"]

    with pytest.raises(ValidationError):
        GameStateResponse.model_validate(data)
