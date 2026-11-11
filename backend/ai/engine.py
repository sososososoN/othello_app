from math import inf
from time import perf_counter

from backend.ai.models import MoveEvaluation, SearchResult, SearchStats
from backend.ai.search import apply_move, minimax, order_moves
from backend.game import (
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
    candidates: list[MoveEvaluation] | None = None,
    player: int = WHITE,
) -> tuple[Position | None, int | None]:
    """最善手を選択し、必要に応じて候補手の解析情報を収集する。"""

    if player not in (BLACK, WHITE):
        raise ValueError("Invalid CPU player")

    moves = order_moves(
        get_valid_moves(board, player),
        player,
    )

    if not moves:
        return None, None

    best_move = moves[0]
    best_score = -inf

    for y, x in moves:
        flippable = get_flippable_stones(
            board,
            y,
            x,
            player,
        )

        penalty = sum(count_adjacent_empty_cells(board, fy, fx) for fy, fx in flippable)

        next_board = apply_move(board, y, x, player)

        score = minimax(
            next_board,
            depth,
            -inf,
            inf,
            3 - player,
            stats=stats,
            maximizing_player=player,
        )

        total_score = score - penalty * 2

        # 解析時のみ候補手ごとの結果を保存する
        if candidates is not None:
            candidates.append(
                MoveEvaluation(
                    move=(y, x),
                    minimax_score=score,
                    penalty=penalty,
                    total_score=total_score,
                )
            )

        # 同点なら先に探索した候補を優先する
        if total_score > best_score:
            best_score = total_score
            best_move = (y, x)

    return best_move, int(best_score)


def choose_cpu_move(
    board: Board, depth: int | None = None, player: int = WHITE
) -> Position | None:
    """通常対戦用。CPUの最善手だけを返す。"""
    # 既存仕様：合法手がなければ深さの検証前にNoneを返す
    if player not in (BLACK, WHITE):
        raise ValueError("Invalid CPU player")

    if not get_valid_moves(board, player):
        return None

    resolved_depth = _resolve_depth(board, depth)
    best_move, _ = _select_best_move(board, resolved_depth, player=player)
    return best_move


def analyze_cpu_move(
    board: Board,
    depth: int | None = None,
    player: int = WHITE,
) -> SearchResult:
    """最善手・探索統計・候補手ごとの評価結果を返す。"""

    if player not in (BLACK, WHITE):
        raise ValueError("Invalid CPU player")

    start = perf_counter()
    resolved_depth = _resolve_depth(board, depth)

    # 探索統計を記録するオブジェクト
    stats = SearchStats()

    # 各候補手の評価結果を保存するリスト
    candidates: list[MoveEvaluation] = []

    # 同じリストを内部関数に渡して候補手を収集
    best_move, score = _select_best_move(
        board,
        resolved_depth,
        stats=stats,
        candidates=candidates,
        player=player,
    )

    return SearchResult(
        best_move=best_move,
        score=score,
        depth=resolved_depth,
        nodes_visited=stats.nodes_visited,
        cutoffs=stats.cutoffs,
        elapsed_ms=(perf_counter() - start) * 1000,
        candidates=tuple(candidates),
    )
