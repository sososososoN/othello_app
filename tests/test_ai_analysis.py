import pytest

from ai.engine import analyze_cpu_move, choose_cpu_move
from game import BLACK, Game, create_board


@pytest.mark.parametrize("depth", [0, 1, 2])
def test_analysis_selects_same_move(depth: int) -> None:
    """解析用関数と通常のCPUが同じ手を選択する。"""
    game = Game()
    assert game.place(2, 3)

    expected = choose_cpu_move(game.board, depth=depth)
    result = analyze_cpu_move(game.board, depth=depth)

    assert result.best_move == expected
    assert result.depth == depth
    assert result.score is not None


def test_analysis_collects_statistics() -> None:
    """探索ノード数と処理時間が記録される。"""
    game = Game()
    assert game.place(2, 3)

    result = analyze_cpu_move(game.board, depth=2)

    assert result.nodes_visited > 0
    assert result.cutoffs >= 0
    assert result.elapsed_ms >= 0


def test_analysis_does_not_mutate_board() -> None:
    """解析しても元の盤面は変更されない。"""
    game = Game()
    assert game.place(2, 3)

    original = [row.copy() for row in game.board]

    analyze_cpu_move(game.board, depth=1)

    assert game.board == original


def test_analysis_without_legal_moves() -> None:
    """合法手がない場合は着手・評価値をNoneにする。"""
    board = [[BLACK] * 8 for _ in range(8)]

    result = analyze_cpu_move(board, depth=1)

    assert result.best_move is None
    assert result.score is None
    assert result.nodes_visited == 0
    assert result.cutoffs == 0


def test_analysis_rejects_negative_depth() -> None:
    """不正な探索深さを拒否する。"""
    with pytest.raises(ValueError, match="Depth must be non-negative"):
        analyze_cpu_move(create_board(), depth=-1)
