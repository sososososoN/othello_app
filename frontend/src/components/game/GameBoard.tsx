
import type { Board, Cell, Position } from "@/types/game";

// 親コンポーネントから受け取るデータの型
type GameBoardProps = {
  board: Board;
  validMoves: readonly Position[];
};

// 石の種類に応じて日本語の名前を返す
function getStoneName(cell: Cell): string {
  switch (cell) {
    case 1:
      return "黒石";
    case 2:
      return "白石";
    default:
      return "空きマス";
  }
}

export function GameBoard({
  board,
  validMoves,
}: GameBoardProps) {
  // 合法手をSetに変換して検索しやすくする。
  // 例: [2, 3] → "2,3"
  const validMoveKeys = new Set(
    validMoves.map(([y, x]) => `${y},${x}`),
  );

  return (
    <div
      role="grid"
      aria-label="オセロの盤面"
      aria-readonly="true"
      aria-rowcount={8}
      aria-colcount={8}
      className="grid aspect-square w-full max-w-xl grid-cols-8 gap-0.5 rounded-xl border-4 border-board-border bg-board-border p-1"
    >
      {board.map((row, y) =>
        row.map((cell, x) => {
          const isValidMove =
            cell === 0 && validMoveKeys.has(`${y},${x}`);

          return (
            <div
              key={`${y}-${x}`}
              role="gridcell"
              aria-rowindex={y + 1}
              aria-colindex={x + 1}
              aria-label={`${y + 1}行${x + 1}列: ${
                isValidMove ? "合法手" : getStoneName(cell)
              }`}
              className="flex aspect-square items-center justify-center bg-board"
            >
              {/* 黒石・白石を円形で表示 */}
              {cell !== 0 ? (
                <span
                  aria-hidden="true"
                  className={`block size-[76%] rounded-full shadow-md ${
                    cell === 1
                      ? "bg-stone-black"
                      : "border border-black/15 bg-stone-white"
                  }`}
                />
              ) : isValidMove ? (
                /* 合法手は小さな点で表現 */
                <span
                  aria-hidden="true"
                  className="block size-[24%] rounded-full bg-foreground/45"
                />
              ) : null}
            </div>
          );
        }),
      )}
    </div>
  );
}
