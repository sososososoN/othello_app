from math import inf

from backend.ai.models import SearchStats
from backend.ai.search import minimax
from backend.game import WHITE, create_board


def test_minimax_collects_search_statistics() -> None:
    """統計を渡すと探索ノード数が記録される。"""
    stats = SearchStats()

    score = minimax(
        board=create_board(),
        depth=2,
        alpha=-inf,
        beta=inf,
        player=WHITE,
        stats=stats,
    )

    assert isinstance(score, int)
    assert stats.nodes_visited > 0
    assert stats.cutoffs >= 0


def test_minimax_preserves_result_with_statistics() -> None:
    """統計の有無でMinimaxの評価値が変わらない。"""
    board = create_board()

    original = minimax(board, 2, -inf, inf, WHITE)

    stats = SearchStats()
    measured = minimax(board, 2, -inf, inf, WHITE, stats=stats)

    assert measured == original
    assert stats.nodes_visited > 0
    assert stats.cutoffs >= 0
