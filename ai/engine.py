from math import inf
from time import perf_counter

from ai.models import SearchResult, SearchStats
from ai.search import apply_move, minimax, order_moves
from game import (
    WHITE,
    BLACK,
    EMPTY,
    DIRECTIONS,
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


def choose_cpu_move(
    board: Board,
    depth: int | None = None,
) -> Position | None:
    """Minimax探索によりCPU（白）の着手を選択する。"""
    moves = order_moves(
        board,
        get_valid_moves(board, WHITE),
        WHITE,
    )

    if not moves:
        return None

    stone_count = sum(cell != EMPTY for row in board for cell in row)

    if depth is None:
        depth = 5 if stone_count > 48 else 4

    if depth < 0:
        raise ValueError("Depth must be non-negative")

    best_move = moves[0]
    best_score = -inf

    for y, x in moves:
        flippable = get_flippable_stones(board, y, x, WHITE)

        penalty = sum(count_adjacent_empty_cells(board, fy, fx) for fy, fx in flippable)

        next_board = apply_move(board, y, x, WHITE)

        score = minimax(
            next_board,
            depth,
            -inf,
            inf,
            1,  # BLACK
        )

        total_score = score - penalty * 2

        if total_score > best_score:
            best_score = total_score
            best_move = (y, x)

    return best_move


def analyze_cpu_move(
    board: Board,
    depth: int | None = None,
) -> SearchResult:
    """CPUの着手選択と探索統計をまとめて返す。"""

    # 既存のCPUと同じ探索深さの決定方法を使う
    stone_count = sum(cell != EMPTY for row in board for cell in row)

    if depth is None:
        depth = 5 if stone_count > 48 else 4

    # 不正な探索深さを検証する
    if depth < 0:
        raise ValueError("Depth must be non-negative")

    # CPU（白）の合法手を取得し、既存と同じ順序で並べる
    moves = order_moves(
        board,
        get_valid_moves(board, WHITE),
        WHITE,
    )

    # 探索統計はすべての候補手で共有する
    stats = SearchStats()

    # CPUの処理時間を計測する
    start = perf_counter()

    if not moves:
        return SearchResult(
            best_move=None,
            score=None,
            depth=depth,
            nodes_visited=0,
            cutoffs=0,
            elapsed_ms=(perf_counter() - start) * 1000,
        )

    best_move = moves[0]
    best_score = -inf

    for y, x in moves:
        # 着手によって反転する石を取得
        flippable = get_flippable_stones(
            board,
            y,
            x,
            WHITE,
        )

        # 既存CPUと同じペナルティを計算
        penalty = sum(count_adjacent_empty_cells(board, fy, fx) for fy, fx in flippable)

        # 元の盤面を変更せず、着手後の盤面を作成
        next_board = apply_move(
            board,
            y,
            x,
            WHITE,
        )

        # Minimax探索を実行し、統計を収集
        score = minimax(
            next_board,
            depth,
            -inf,
            inf,
            BLACK,
            stats=stats,
        )

        # 既存CPUと同じ最終評価値
        total_score = score - penalty * 2

        # 同点では更新しないことで既存の選択順を維持
        if total_score > best_score:
            best_score = total_score
            best_move = (y, x)

    return SearchResult(
        best_move=best_move,
        score=int(best_score),
        depth=depth,
        nodes_visited=stats.nodes_visited,
        cutoffs=stats.cutoffs,
        elapsed_ms=(perf_counter() - start) * 1000,
    )
