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
          className="grid aspect-square min-w-0 flex-1 grid-cols-8 gap-px rounded-sm border-[7px] border-board-border bg-board-border"
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
                      className={`block size-[78%] rounded-full ${
                        cell === 1
                          ? // 黒石：表面のわずかな光と落ち影を表現
                            "bg-stone-black shadow-[inset_0_1px_1px_rgba(255,255,255,0.15),0_2px_3px_rgba(0,0,0,0.25)]"
                          : // 白石：輪郭を保ちつつ陶器のような陰影を表現
                            "border border-black/10 bg-stone-white shadow-[inset_0_-2px_3px_rgba(0,0,0,0.08),0_2px_3px_rgba(0,0,0,0.18)]"
                      }`}
                    />
                  ) : isValidMove ? (
                    <button
                      type="button"
                      aria-label={`${label}に置く`}
                      disabled={disabled}
                      onClick={() => onSelectMove([y, x])}
                      className="group flex size-full cursor-pointer items-center justify-center transition-colors hover:bg-white/10 focus-visible:z-10 focus-visible:outline-2 focus-visible:outline-offset-[-3px] focus-visible:outline-stone-white disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      <span
                        aria-hidden="true"
                        className="block size-[18%] rounded-full bg-stone-white/55 transition-transform group-hover:scale-125"
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
