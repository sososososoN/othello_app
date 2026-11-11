import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { GameBoard } from "./GameBoard";
import type { Board, Position } from "@/types/game";

const board: Board = [
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 2, 1, 0, 0, 0],
  [0, 0, 0, 1, 2, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
];

const validMoves: Position[] = [[2, 3]];

describe("GameBoard", () => {
  it("8×8の盤面を描画する", () => {
    render(<GameBoard board={board} validMoves={validMoves} onSelectMove={vi.fn()} />);

    expect(screen.getAllByRole("gridcell")).toHaveLength(64);
  });

  it("合法手をクリックすると座標を通知する", async () => {
    const user = userEvent.setup();
    const onSelectMove = vi.fn();

    render(
      <GameBoard board={board} validMoves={validMoves} onSelectMove={onSelectMove} />,
    );

    await user.click(
      screen.getByRole("button", {
        name: /3行4列/,
      }),
    );

    expect(onSelectMove).toHaveBeenCalledWith([2, 3]);
    expect(onSelectMove).toHaveBeenCalledTimes(1);
  });

  it("disabledの場合は着手できない", async () => {
    const user = userEvent.setup();
    const onSelectMove = vi.fn();

    render(
      <GameBoard
        board={board}
        validMoves={validMoves}
        onSelectMove={onSelectMove}
        disabled
      />,
    );

    const button = screen.getByRole("button");

    expect(button).toBeDisabled();

    await user.click(button);

    expect(onSelectMove).not.toHaveBeenCalled();
  });

  it("盤面の上下方向の座標ラベルを表示する", () => {
    render(<GameBoard board={board} validMoves={[]} onSelectMove={vi.fn()} />);

    for (const column of "ABCDEFGH") {
      expect(screen.getByText(column)).toBeInTheDocument();
    }

    for (let row = 1; row <= 8; row++) {
      expect(screen.getByText(String(row))).toBeInTheDocument();
    }

    expect(screen.getAllByRole("gridcell")).toHaveLength(64);
  });
});
