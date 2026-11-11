import pytest

from backend.ai.engine import analyze_cpu_move, choose_cpu_move
from backend.game import BLACK, Game, create_board


@pytest.mark.parametrize("depth", [0, 1, 2, 3])
def test_analysis_selects_same_move(depth: int) -> None:
    """解析用関数と通常のCPUが同じ手を選択する。"""
    game = Game()
    assert game.place(2, 3)

    expected = choose_cpu_move(game.board, depth=depth)
    result = analyze_cpu_move(game.board, depth=depth)

    assert result.best_move == expected
    assert result.score is not None
    assert result.nodes_visited > 0
    assert result.depth == depth


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

    analyze_cpu_move(game.board, depth=2)

    assert game.board == original


def test_analysis_without_legal_moves() -> None:
    """合法手がない場合は着手・評価値をNoneにする。"""
    board = [[BLACK] * 8 for _ in range(8)]

    result = analyze_cpu_move(board, depth=2)

    assert result.best_move is None
    assert result.score is None
    assert result.nodes_visited == 0
    assert result.cutoffs == 0


def test_analysis_rejects_negative_depth() -> None:
    """不正な探索深さを拒否する。"""
    with pytest.raises(ValueError, match="Depth must be non-negative"):
        analyze_cpu_move(create_board(), depth=-1)


def test_analysis_contains_all_legal_moves() -> None:
    """すべての合法手が候補手一覧に含まれることを確認する。"""
    from backend.game import WHITE, get_valid_moves

    game = Game()
    assert game.place(2, 3)

    result = analyze_cpu_move(game.board, depth=1)

    expected_moves = set(get_valid_moves(game.board, WHITE))
    actual_moves = {item.move for item in result.candidates}

    assert actual_moves == expected_moves
    assert len(result.candidates) == len(expected_moves)


def test_candidate_evaluation_consistency() -> None:
    """各候補手の総合評価値が計算式と一致する。"""
    game = Game()
    assert game.place(2, 3)

    result = analyze_cpu_move(game.board, depth=2)

    assert result.candidates

    for candidate in result.candidates:
        assert candidate.total_score == (
            candidate.minimax_score - candidate.penalty * 2
        )


def test_best_move_has_highest_score() -> None:
    """最善手が候補手の中で最大の総合評価値を持つ。"""
    game = Game()
    assert game.place(2, 3)

    result = analyze_cpu_move(game.board, depth=2)

    best_candidate = max(
        result.candidates,
        key=lambda candidate: candidate.total_score,
    )

    assert result.best_move == best_candidate.move
    assert result.score == best_candidate.total_score


def test_no_legal_moves_has_no_candidates() -> None:
    """合法手がなければ候補手一覧は空になる。"""
    board = [[BLACK] * 8 for _ in range(8)]

    result = analyze_cpu_move(board, depth=1)

    assert result.best_move is None
    assert result.candidates == ()


def test_candidate_results_are_immutable() -> None:
    """探索完了後に候補手の評価値を変更できない。"""
    from dataclasses import FrozenInstanceError

    game = Game()
    assert game.place(2, 3)

    result = analyze_cpu_move(game.board, depth=1)

    with pytest.raises(FrozenInstanceError):
        result.candidates[0].total_score = 999
