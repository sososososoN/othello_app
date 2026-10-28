
from game import BLACK, WHITE
from storage import GameStore


def test_create_game() -> None:
    store = GameStore()

    game_id, record = store.create()

    assert isinstance(game_id, str)
    assert len(game_id) == 32
    assert record.game.turn == BLACK
    assert record.mode == "pvp"
    assert store.count() == 1


def test_get_game() -> None:
    store = GameStore()

    game_id, record = store.create()

    assert store.get(game_id) is record


def test_unknown_game() -> None:
    store = GameStore()

    assert store.get("unknown") is None


def test_games_are_independent() -> None:
    store = GameStore()

    id_a, game_a = store.create()
    id_b, game_b = store.create()

    assert id_a != id_b
    assert game_a is not game_b
    assert game_a.game is not game_b.game

    assert game_a.game.place(2, 3) is True

    assert game_a.game.turn == WHITE
    assert game_b.game.turn == BLACK


def test_delete_game() -> None:
    store = GameStore()

    game_id, _ = store.create()

    assert store.delete(game_id) is True
    assert store.get(game_id) is None
    assert store.count() == 0


def test_delete_unknown_game() -> None:
    store = GameStore()

    assert store.delete("unknown") is False


def test_separate_stores() -> None:
    store_a = GameStore()
    store_b = GameStore()

    game_id, _ = store_a.create()

    assert store_a.get(game_id) is not None
    assert store_b.get(game_id) is None
