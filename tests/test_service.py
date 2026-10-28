
import pytest

from game import BLACK, WHITE, Game
from service import GameError, GameService
from storage import GameRecord


def test_initial_state() -> None:
    service = GameService(GameRecord())
    state = service.state()

    assert state["turn"] == BLACK
    assert state["mode"] == "pvp"
    assert len(state["valid_moves"]) == 4


def test_valid_move() -> None:
    service = GameService(GameRecord())

    service.play(2, 3)

    state = service.state()

    assert state["board"][2][3] == BLACK
    assert state["board"][3][3] == BLACK
    assert state["turn"] == WHITE


def test_illegal_move() -> None:
    service = GameService(GameRecord())

    with pytest.raises(GameError) as exc_info:
        service.play(0, 0)

    assert exc_info.value.status_code == 400
    assert str(exc_info.value) == "Illegal move"


def test_change_mode_before_start() -> None:
    service = GameService(GameRecord())

    service.change_mode("pvc")

    assert service.state()["mode"] == "pvc"


def test_change_mode_after_start() -> None:
    service = GameService(GameRecord())
    service.play(2, 3)

    with pytest.raises(GameError) as exc_info:
        service.change_mode("pvc")

    assert exc_info.value.status_code == 409


def test_invalid_mode() -> None:
    service = GameService(GameRecord())

    with pytest.raises(GameError) as exc_info:
        service.change_mode("invalid")

    assert exc_info.value.status_code == 400


def test_cpu_move() -> None:
    # CPUは必ず(2,2)を選択するようにする
    service = GameService(
        GameRecord(mode="pvc"),
        cpu_selector=lambda board: (2, 2),
    )

    service.play(2, 3)
    state = service.state()

    assert state["board"][2][2] == WHITE
    assert state["turn"] == BLACK


def test_reset_preserves_mode() -> None:
    service = GameService(GameRecord(mode="pvc"))

    service.reset()

    assert service.state()["board"] == Game().board
    assert service.state()["mode"] == "pvc"


def test_state_is_snapshot() -> None:
    service = GameService(GameRecord())

    state = service.state()
    state["board"][3][3] = 0

    assert service.state()["board"][3][3] == WHITE
