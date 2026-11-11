from dataclasses import dataclass

from backend.game import Position


@dataclass
class SearchStats:
    """探索中に収集する統計情報。"""

    nodes_visited: int = 0
    cutoffs: int = 0


@dataclass(frozen=True)
class MoveEvaluation:
    """CPUの候補手1つに対する評価結果。"""

    move: Position
    minimax_score: int
    penalty: int
    total_score: int


@dataclass(frozen=True)
class SearchResult:
    """CPUが実行した探索の結果。"""

    best_move: Position | None
    score: int | None
    depth: int
    nodes_visited: int
    cutoffs: int
    elapsed_ms: float
    candidates: tuple[MoveEvaluation, ...] = ()
