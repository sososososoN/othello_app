
/**
 * Python側のgame.py / schemas.pyに対応した型定義。
 */

// 0: 空きマス、1: 黒石、2: 白石
export type Cell = 0 | 1 | 2;

// 1行は8マス固定。
// TypeScriptで要素数を明示するためタプル型を使う。
export type BoardRow = [
  Cell, Cell, Cell, Cell,
  Cell, Cell, Cell, Cell,
];

// オセロ盤は8行固定。
export type Board = [
  BoardRow, BoardRow, BoardRow, BoardRow,
  BoardRow, BoardRow, BoardRow, BoardRow,
];

// 座標は[y, x]。
// yが縦方向、xが横方向。
export type Position = readonly [number, number];

// ゲーム全体の状態を表す型
export type GameState = {
  board: Board;
  turn: Cell;
  message: string;
  mode: "pvp" | "pvc";
  difficulty: "easy" | "normal" | "hard";
  valid_moves: Position[];
};
