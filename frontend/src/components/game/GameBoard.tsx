
import type { Board, Cell, Position } from "@/types/game";

// 親コンポーネントから受け取るデータの型
type GameBoardProps = {
  board: Board;
  validMoves: readonly Position[];
  onSelectMove: (position: Position) => void;
  disabled?: boolean;
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
  onSelectMove,
  disabled = false,
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

          const label = `${y + 1}行${x + 1}列: ${
            isValidMove ? "合法手" : getStoneName(cell)
          }`;

          return (
            <div
              key={`${y}-${x}`}
              role="gridcell"
              aria-rowindex={y + 1}
              aria-colindex={x + 1}
              
              className="flex aspect-square items-center justify-center bg-board"
            >
              {/* 黒石・白石を円形で表示 */}
              {cell !== 0 ? (
                <span
                  role="img"
                  aria-label={label}
                  className={`block size-[76%] rounded-full shadow-md ${
                    cell === 1
                      ? "bg-stone-black"
                      : "border border-black/15 bg-stone-white"
                  }`}
                />
              ) : isValidMove ? (
                /* 合法手は小さな点で表現 */
                <button
                  type="button"
                  aria-label={`${label}に置く`}
                  disabled={disabled}
                  onClick={() => onSelectMove([y, x])}
                  className="flex size-full cursor-pointer items-center justify-center transition-colors hover:bg-white/10 focus-visible:z-10 focus-visible:outline-2 focus-visible:outline-offset-[-3px] focus-visible:outline-primary disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <span
                    aria-hidden="true"
                    className="block size-[24%] rounded-full bg-foreground/45 transition-transform hover:scale-125"
                  />
                </button>
              ) : (
                <span
                  aria-label={label}
                  className="block size-full"
                />
              )}
            </div>
          );
        }),
      )}
    </div>
  );
}
