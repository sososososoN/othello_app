import pytest

from game import BLACK, WHITE, Game, Board, Position
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


def test_difficulty_defaults_to_normal() -> None:
    service = GameService(GameRecord())
    assert service.state()["difficulty"] == "normal"


def test_change_difficulty_in_pvc() -> None:
    record = GameRecord(mode="pvc")
    service = GameService(record)

    service.change_difficulty("hard")

    assert service.state()["difficulty"] == "hard"


def test_change_difficulty_requires_pvc() -> None:
    service = GameService(GameRecord())

    with pytest.raises(GameError) as exc_info:
        service.change_difficulty("easy")

    assert exc_info.value.status_code == 409


def test_difficulty_cannot_change_after_move() -> None:
    record = GameRecord(mode="pvc")
    service = GameService(
        record,
        cpu_selector=lambda board: (2, 4),
    )

    service.play(2, 3)

    with pytest.raises(GameError) as exc_info:
        service.change_difficulty("hard")

    assert exc_info.value.status_code == 409
    assert record.difficulty == "normal"


def test_reset_preserves_difficulty() -> None:
    record = GameRecord(mode="pvc")
    service = GameService(record)

    service.change_difficulty("easy")
    service.reset()

    assert service.state()["difficulty"] == "easy"
    assert service.state()["turn"] == BLACK


def test_manual_cpu_turn_matches_automatic_cpu_turn() -> None:
    """自動CPU着手と手動CPU着手が同じ盤面になる。"""

    # CPUが必ず同じ合法手を選ぶよう固定する
    def selector(board: Board) -> Position:
        return (2, 2)

    automatic = GameService(
        GameRecord(mode="pvc"),
        cpu_selector=selector,
    )

    manual = GameService(
        GameRecord(mode="pvc"),
        cpu_selector=selector,
    )

    # 自動方式：人間の着手とCPUの着手をまとめて実行
    automatic.play(2, 3)

    # 分離方式：人間の着手とCPUの着手を別々に実行
    manual.play_human(2, 3)
    manual.play_cpu()

    # 両方式の対局状態が一致することを確認
    assert automatic.state() == manual.state()


def test_manual_cpu_turn_rejects_pvp() -> None:
    """PvPモードではCPUを実行できない。"""
    service = GameService(GameRecord(mode="pvp"))

    with pytest.raises(GameError) as exc_info:
        service.play_cpu()

    assert exc_info.value.status_code == 409


def test_cpu_error_rolls_back_game() -> None:
    """不正なCPU着手が発生した場合、盤面を元に戻す。"""

    # (0, 0)は初期局面付近では合法手ではない
    service = GameService(
        GameRecord(mode="pvc"),
        cpu_selector=lambda board: (0, 0),
    )

    before = service.state()

    with pytest.raises(
        RuntimeError,
        match="CPU selected an illegal move",
    ):
        # 人間の着手後にCPUが不正な手を返す
        service.play(2, 3)

    # 人間の着手も含めて元の状態に戻る
    assert service.state() == before


def test_play_returns_updated_snapshot() -> None:
    """更新メソッドの戻り値に着手後の状態が含まれる。"""
    service = GameService(GameRecord())

    state = service.play(2, 3)

    assert state["board"][2][3] == BLACK
    assert state["turn"] == WHITE

    # 戻り値を変更しても実際の対局には影響しない
    state["board"][2][3] = 0
    assert service.state()["board"][2][3] == BLACK


def test_change_mode_same_value_returns_state() -> None:
    """同じモードを指定しても正しい状態を返す。"""
    service = GameService(GameRecord())

    state = service.change_mode("pvp")

    assert state["mode"] == "pvp"
    assert state == service.state()


def test_persist_failure_does_not_return_success() -> None:
    """保存失敗時は例外を送出して状態を元に戻す。"""
    record = GameRecord()

    def fail_persist() -> None:
        raise OSError("Database write failed")

    # 保存先の障害を再現
    record.save_callback = fail_persist
    service = GameService(record)
    before = service.state()

    with pytest.raises(OSError, match="Database write failed"):
        service.play(2, 3)

    assert service.state() == before


def test_failed_persistence_restores_version() -> None:
    """永続化に失敗した場合はversionも復元する。"""
    from service import GameService
    from storage import GameRecord

    record = GameRecord()
    service = GameService(record)

    # 最初はversion=3だったとする
    record.version = 3
    before = service.state()

    def failing_save() -> None:
        # 保存処理が途中でメモリのversionを変更した状況を再現
        record.version = 4
        raise RuntimeError("Simulated persistence failure")

    record.save_callback = failing_save

    # 保存失敗時に例外が伝播することを確認
    with pytest.raises(
        RuntimeError,
        match="Simulated persistence failure",
    ):
        service.play(2, 3)

    # 盤面とversionの両方が元に戻る
    assert service.state() == before
    assert record.version == 3
