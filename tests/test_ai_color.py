from math import inf

import pytest

from ai.engine import analyze_cpu_move, choose_cpu_move
from ai.evaluation import evaluate_board
from ai.search import minimax
from game import BLACK, WHITE, Game, create_board, get_valid_moves


@pytest.mark.parametrize("player", [BLACK, WHITE])
def test_cpu_move_is_legal_for_both_colors(player: int) -> None:
    """黒CPU・白CPUともに合法手を返す。"""
    game = Game()

    if player == WHITE:
        # 白が着手できる局面に進める
        assert game.place(2, 3)

    board_before = [row.copy() for row in game.board]

    move = choose_cpu_move(
        game.board,
        depth=1,
        player=player,
    )

    assert move is not None
    assert move in get_valid_moves(game.board, player)

    # 探索によって盤面が変更されない
    assert game.board == board_before


@pytest.mark.parametrize("player", [BLACK, WHITE])
def test_analysis_matches_cpu(player: int) -> None:
    """通常のCPUと解析結果が同じ手を選ぶ。"""
    game = Game()

    if player == WHITE:
        assert game.place(2, 3)

    expected = choose_cpu_move(
        game.board,
        depth=1,
        player=player,
    )

    result = analyze_cpu_move(
        game.board,
        depth=1,
        player=player,
    )

    assert result.best_move == expected
    assert {candidate.move for candidate in result.candidates} == set(
        get_valid_moves(game.board, player)
    )


def test_evaluation_changes_sign_by_perspective() -> None:
    """同じ局面を黒・白から見ると評価値の符号が反転する。"""
    game = Game()
    assert game.place(2, 3)

    white_score = evaluate_board(game.board, WHITE)
    black_score = evaluate_board(game.board, BLACK)

    assert black_score == -white_score


def test_minimax_supports_black_as_maximizer() -> None:
    """Minimaxが黒視点でも評価できる。"""
    board = create_board()

    result = minimax(
        board,
        depth=2,
        alpha=-inf,
        beta=inf,
        player=BLACK,
        maximizing_player=BLACK,
    )

    assert isinstance(result, int)


@pytest.mark.parametrize("player", [0, 3, -1])
def test_invalid_cpu_color_is_rejected(player: int) -> None:
    """不正なプレイヤー色を受け付けない。"""
    board = create_board()

    with pytest.raises(ValueError, match="Invalid CPU player"):
        choose_cpu_move(board, depth=1, player=player)

    with pytest.raises(ValueError, match="Invalid CPU player"):
        analyze_cpu_move(board, depth=1, player=player)


@pytest.mark.parametrize("player", [BLACK, WHITE])
def test_cpu_move_is_deterministic(player: int) -> None:
    """同じ盤面と条件では同じ着手を返す。"""
    game = Game()

    if player == WHITE:
        assert game.place(2, 3)

    first = choose_cpu_move(game.board, depth=1, player=player)
    second = choose_cpu_move(game.board, depth=1, player=player)

    assert first is not None
    assert first == second


def test_terminal_evaluation_changes_sign() -> None:
    """終局時も黒視点と白視点の評価値が反転する。"""

    # 全マスが黒なら黒の勝利
    board = [[BLACK] * 8 for _ in range(8)]

    white_score = evaluate_board(board, WHITE)
    black_score = evaluate_board(board, BLACK)

    # 黒視点では勝利なのでプラス
    assert black_score > 0

    # 白視点では敗北なのでマイナス
    assert white_score < 0

    # 評価値はちょうど符号反転する
    assert black_score == -white_score
