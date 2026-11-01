import pytest

from ai.engine import analyze_cpu_move, choose_cpu_move
from game import BLACK, Game, create_board


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


"""CPUの着手選択と解析結果の取得。"""

from math import inf
from time import perf_counter

from ai.models import SearchResult, SearchStats
from ai.search import apply_move, minimax, order_moves
from game import (
    BLACK,
    WHITE,
    DIRECTIONS,
    EMPTY,
    Board,
    Position,
    get_flippable_stones,
    get_valid_moves,
)

DIFFICULTY_DEPTH: dict[str, int] = {
    "easy": 1,
    "normal": 3,
    "hard": 5,
}


def count_adjacent_empty_cells(
    board: Board,
    y: int,
    x: int,
) -> int:
    """指定したマスの周囲8方向にある空きマスを数える。"""
    count = 0

    for dy, dx in DIRECTIONS:
        ny, nx = y + dy, x + dx

        if 0 <= ny < 8 and 0 <= nx < 8 and board[ny][nx] == EMPTY:
            count += 1

    return count


def _resolve_depth(board: Board, depth: int | None) -> int:
    """省略された探索深さを盤面の石数から決定する。"""
    if depth is None:
        stone_count = sum(cell != EMPTY for row in board for cell in row)
        depth = 5 if stone_count > 48 else 4

    if depth < 0:
        raise ValueError("Depth must be non-negative")

    return depth


def _select_best_move(
    board: Board,
    depth: int,
    stats: SearchStats | None = None,
) -> tuple[Position | None, int | None]:
    """合法手を探索して、最善手と最終評価値を返す。"""
    moves = order_moves(
        board,
        get_valid_moves(board, WHITE),
        WHITE,
    )

    if not moves:
        return None, None

    best_move = moves[0]
    best_score = -inf

    for y, x in moves:
        # 既存CPUと同じペナルティを計算
        flippable = get_flippable_stones(board, y, x, WHITE)

        penalty = sum(count_adjacent_empty_cells(board, fy, fx) for fy, fx in flippable)

        # 元の盤面を変更せず着手後の盤面を生成
        next_board = apply_move(board, y, x, WHITE)

        # 統計が必要なときだけstatsを渡す
        score = minimax(
            next_board,
            depth,
            -inf,
            inf,
            BLACK,
            stats=stats,
        )

        total_score = score - penalty * 2

        # 同点では更新しない（既存の挙動を維持）
        if total_score > best_score:
            best_score = total_score
            best_move = (y, x)

    return best_move, int(best_score)


def choose_cpu_move(
    board: Board,
    depth: int | None = None,
) -> Position | None:
    """通常対戦用。CPUの最善手だけを返す。"""
    # 既存仕様：合法手がなければ深さの検証前にNoneを返す
    if not get_valid_moves(board, WHITE):
        return None

    resolved_depth = _resolve_depth(board, depth)
    best_move, _ = _select_best_move(
        board,
        resolved_depth,
    )
    return best_move


def analyze_cpu_move(
    board: Board,
    depth: int | None = None,
) -> SearchResult:
    """解析用。着手・評価値・探索統計を返す。"""
    start = perf_counter()
    resolved_depth = _resolve_depth(board, depth)
    stats = SearchStats()

    best_move, score = _select_best_move(
        board,
        resolved_depth,
        stats=stats,
    )

    return SearchResult(
        best_move=best_move,
        score=score,
        depth=resolved_depth,
        nodes_visited=stats.nodes_visited,
        cutoffs=stats.cutoffs,
        elapsed_ms=(perf_counter() - start) * 1000,
    )
