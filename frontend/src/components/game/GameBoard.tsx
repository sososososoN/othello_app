import type { Board, Cell, Position } from "@/types/game";

type GameBoardProps = {
  board: Board;
  validMoves: readonly Position[];
  onSelectMove: (position: Position) => void;
  disabled?: boolean;
};

const columns = ["A", "B", "C", "D", "E", "F", "G", "H"] as const;

const rows = [1, 2, 3, 4, 5, 6, 7, 8] as const;

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
  const validMoveKeys = new Set(validMoves.map(([y, x]) => `${y},${x}`));

  return (
    <div className="w-full max-w-xl">
      <div
        aria-hidden="true"
        className="grid grid-cols-[1.5rem_repeat(8,minmax(0,1fr))] pb-1"
      >
        <span />

        {columns.map((column) => (
          <span
            key={column}
            className="text-center text-xs font-semibold text-muted-foreground"
          >
            {column}
          </span>
        ))}
      </div>

      <div className="flex">
        <div aria-hidden="true" className="grid w-6 shrink-0 grid-rows-8">
          {rows.map((row) => (
            <span
              key={row}
              className="flex items-center justify-center text-xs font-semibold text-muted-foreground"
            >
              {row}
            </span>
          ))}
        </div>
        <div
          role="grid"
          aria-label="オセロの盤面"
          aria-readonly="true"
          aria-rowcount={8}
          aria-colcount={8}
          className="grid aspect-square min-w-0 flex-1 grid-cols-8 gap-0.5 rounded-xl border-4 border-board-border bg-board-border p-1"
        >
          {board.map((row, y) =>
            row.map((cell, x) => {
              const isValidMove = cell === 0 && validMoveKeys.has(`${y},${x}`);

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
                    <span aria-label={label} className="block size-full" />
                  )}
                </div>
              );
            }),
          )}
        </div>
      </div>
    </div>
  );
}
