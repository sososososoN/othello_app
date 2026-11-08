import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import App from "./App";
import {
  getGameState,
  playCpuMove,
  playHumanMove,
  resetGame,
  startGame,
} from "@/api/client";

import type { GameState } from "@/types/game";

// 追加：実際の通信を実行しないようにする
vi.mock("@/api/client", () => ({
  getGameState: vi.fn(),
  playCpuMove: vi.fn(),
  playHumanMove: vi.fn(),
  resetGame: vi.fn(),
  startGame: vi.fn(),
}));

// テスト共通の初期状態
const initialState: GameState = {
  board: [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 2, 1, 0, 0, 0],
    [0, 0, 0, 1, 2, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
  ],
  turn: 1,
  message: "",
  mode: "pvp",
  difficulty: "normal",
  human_color: 1,
  cpu_color: null,
  valid_moves: [
    [2, 3],
    [3, 2],
    [4, 5],
    [5, 4],
  ],
};

// 各テスト前にモックをリセット
beforeEach(() => {
  vi.resetAllMocks();

  vi.mocked(getGameState).mockResolvedValue(initialState);
  vi.mocked(startGame).mockResolvedValue(initialState);
  vi.mocked(resetGame).mockResolvedValue(initialState);
  vi.mocked(playHumanMove).mockResolvedValue(initialState);
  vi.mocked(playCpuMove).mockResolvedValue(initialState);
});

describe("App", () => {
  it("初回表示でAPIから盤面を取得する", async () => {
    render(<App />);

    expect(await screen.findAllByRole("gridcell")).toHaveLength(64);

    expect(getGameState).toHaveBeenCalledTimes(1);
  });

  it("CPU対戦の先後と難易度を送信する", async () => {
    const user = userEvent.setup();
    render(<App />);

    await screen.findAllByRole("gridcell");

    await user.selectOptions(screen.getByLabelText("対戦モード"), "pvc");

    await user.selectOptions(screen.getByLabelText("CPUの難易度"), "easy");

    await user.selectOptions(screen.getByLabelText("自分の手番"), "second");

    await user.click(
      screen.getByRole("button", {
        name: "対局を開始する",
      }),
    );

    await waitFor(() => {
      expect(startGame).toHaveBeenCalledWith({
        mode: "pvc",
        difficulty: "easy",
        human_order: "second",
      });
    });
  });

  it("PvPで合法手をクリックすると着手APIを呼ぶ", async () => {
    const user = userEvent.setup();
    render(<App />);

    await screen.findAllByRole("gridcell");

    await user.click(
      screen.getByRole("button", {
        name: /3行4列/,
      }),
    );

    await waitFor(() => {
      expect(playHumanMove).toHaveBeenCalledWith({
        y: 2,
        x: 3,
      });
    });

    expect(playCpuMove).not.toHaveBeenCalled();
  });

  it("PvCでは人間の着手後にCPUを実行する", async () => {
    const user = userEvent.setup();

    const pvcState: GameState = {
      ...initialState,
      mode: "pvc",
      cpu_color: 2,
    };

    const cpuTurnState: GameState = {
      ...pvcState,
      turn: 2,
    };

    vi.mocked(getGameState).mockResolvedValue(pvcState);
    vi.mocked(playHumanMove).mockResolvedValue(cpuTurnState);
    vi.mocked(playCpuMove).mockResolvedValue(pvcState);

    render(<App />);

    await screen.findAllByRole("gridcell");

    await user.click(
      screen.getByRole("button", {
        name: /3行4列/,
      }),
    );

    await waitFor(() => {
      expect(playHumanMove).toHaveBeenCalledTimes(1);
      expect(playCpuMove).toHaveBeenCalledTimes(1);
    });
  });

  it("CPUの手番では人間の着手を禁止する", async () => {
    const cpuTurnState: GameState = {
      ...initialState,
      mode: "pvc",
      turn: 2,
      cpu_color: 2,
    };

    vi.mocked(getGameState).mockResolvedValue(cpuTurnState);

    render(<App />);

    await screen.findAllByRole("gridcell");

    expect(screen.getByRole("button", { name: /3行4列/ })).toBeDisabled();

    expect(playHumanMove).not.toHaveBeenCalled();
  });

  it("リセットすると人間先攻へ戻る", async () => {
    const user = userEvent.setup();

    const secondState: GameState = {
      ...initialState,
      mode: "pvc",
      human_color: 2,
      cpu_color: 1,
      turn: 2,
    };

    const resetState: GameState = {
      ...initialState,
      mode: "pvc",
      cpu_color: 2,
    };

    vi.mocked(getGameState).mockResolvedValue(secondState);
    vi.mocked(resetGame).mockResolvedValue(resetState);

    render(<App />);

    await screen.findAllByRole("gridcell");

    expect(screen.getByLabelText("自分の手番")).toHaveValue("second");

    await user.click(
      screen.getByRole("button", {
        name: "リセット",
      }),
    );

    await waitFor(() => {
      expect(resetGame).toHaveBeenCalledTimes(1);

      expect(screen.getByLabelText("自分の手番")).toHaveValue("first");
    });
  });

  it("初期通信エラーを表示する", async () => {
    vi.mocked(getGameState).mockRejectedValue(
      new Error("サーバーに接続できませんでした"),
    );

    render(<App />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "サーバーに接続できませんでした",
    );
  });
});
