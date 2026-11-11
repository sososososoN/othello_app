/**
 * Python側のgame.py / schemas.pyに対応した型定義。
 */

// 0: 空きマス、1: 黒石、2: 白石
export type Cell = 0 | 1 | 2;

export type PlayerColor = 1 | 2;

export type GameMode = "pvp" | "pvc";
export type Difficulty = "easy" | "normal" | "hard";
export type HumanOrder = "first" | "second" | "random";

// 1行は8マス固定。
// TypeScriptで要素数を明示するためタプル型を使う。
export type BoardRow = [Cell, Cell, Cell, Cell, Cell, Cell, Cell, Cell];

// オセロ盤は8行固定。
export type Board = [
  BoardRow,
  BoardRow,
  BoardRow,
  BoardRow,
  BoardRow,
  BoardRow,
  BoardRow,
  BoardRow,
];

// 座標は[y, x]。
// yが縦方向、xが横方向。
export type Position = readonly [number, number];

// ゲーム全体の状態を表す型
export type GameState = {
  board: Board;
  turn: Cell;
  message: string;
  mode: GameMode;
  difficulty: Difficulty;
  human_color: PlayerColor;
  cpu_color: PlayerColor | null;
  started: boolean;
  valid_moves: Position[];
};

export type StartGameRequest = {
  mode: GameMode;
  difficulty: Difficulty;
  human_order: HumanOrder;
};

export type MoveRequest = {
  y: number;
  x: number;
};

export type MoveEvaluation = {
  move: Position;
  minimax_score: number;
  penalty: number;
  total_score: number;
};

export type AnalysisResult = {
  best_move: Position | null;
  score: number | null;
  depth: number;
  nodes_visited: number;
  cutoffs: number;
  elapsed_ms: number;
  candidates: MoveEvaluation[];
  analysis_token: string | null;
};
