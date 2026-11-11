import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import App from "./App";
import {
  ApiError,
  getAnalysis,
  getGameState,
  playCpuMove,
  playHumanMove,
  resetGame,
  startGame,
} from "@/api/client";

import type { AnalysisResult, GameState } from "@/types/game";

vi.mock("@/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/client")>();
  return {
    ...actual,
    getAnalysis: vi.fn(),
    getGameState: vi.fn(),
    playCpuMove: vi.fn(),
    playHumanMove: vi.fn(),
    resetGame: vi.fn(),
    startGame: vi.fn(),
  };
});

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
  started: false,
  valid_moves: [
    [2, 3],
    [3, 2],
    [4, 5],
    [5, 4],
  ],
};

const mockAnalysis: AnalysisResult = {
  best_move: [2, 2],
  score: 12,
  depth: 1,
  nodes_visited: 25,
  cutoffs: 3,
  elapsed_ms: 4.5,
  candidates: [
    {
      move: [2, 2],
      minimax_score: 16,
      penalty: 2,
      total_score: 12,
    },
    {
      move: [2, 4],
      minimax_score: 10,
      penalty: 1,
      total_score: 8,
    },
  ],
  analysis_token: "signed-test-token",
};

beforeEach(() => {
  vi.resetAllMocks();

  vi.mocked(getGameState).mockResolvedValue(initialState);
  vi.mocked(startGame).mockResolvedValue({
    ...initialState,
    started: true,
  });
  vi.mocked(resetGame).mockResolvedValue(initialState);
  vi.mocked(playHumanMove).mockResolvedValue(initialState);
  vi.mocked(playCpuMove).mockResolvedValue(initialState);
  vi.mocked(getAnalysis).mockResolvedValue(mockAnalysis);
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
      expect(getAnalysis).toHaveBeenCalledTimes(1);
      expect(playCpuMove).toHaveBeenCalledWith("signed-test-token");
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
  it("CPU解析結果を画面に表示する", async () => {
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

    expect(await screen.findByRole("table")).toBeInTheDocument();

    // (2, 2) = C3
    expect(screen.getAllByText("C3", { exact: true })).toHaveLength(2);

    expect(screen.getByText("候補手の比較")).toBeInTheDocument();

    expect(screen.getByText("25")).toBeInTheDocument();
  });

  // 追加：解析後にリセットしたときの表示確認
  it("リセット後に解析結果が消える", async () => {
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
    vi.mocked(resetGame).mockResolvedValue(pvcState);

    render(<App />);

    await screen.findAllByRole("gridcell");

    await user.click(
      screen.getByRole("button", {
        name: /3行4列/,
      }),
    );

    expect(await screen.findByText("CPUの思考解析")).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", {
        name: "リセット",
      }),
    );

    await waitFor(() => {
      expect(resetGame).toHaveBeenCalledTimes(1);
      expect(screen.queryByRole("table")).not.toBeInTheDocument();
      expect(
        screen.getByText("CPUが着手すると、ここに解析結果を表示します。"),
      ).toBeInTheDocument();
    });
  });

  // 追加：CPU解析に失敗した場合の確認
  it("解析失敗時にCPU着手せずエラーを表示する", async () => {
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

    vi.mocked(getAnalysis).mockRejectedValue(new Error("解析に失敗しました"));

    render(<App />);

    await screen.findAllByRole("gridcell");

    await user.click(
      screen.getByRole("button", {
        name: /3行4列/,
      }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent("解析に失敗しました");

    expect(playCpuMove).not.toHaveBeenCalled();

    // CPUの番が残るため、ユーザーが再実行できる
    expect(
      screen.getByRole("button", {
        name: "CPUの着手を実行",
      }),
    ).toBeInTheDocument();
  });
  it("対局開始後は設定と開始ボタンを操作できない", async () => {
    const user = userEvent.setup();
    render(<App />);
    await screen.findAllByRole("gridcell");
    await user.click(
      screen.getByRole("button", {
        name: "対局を開始する",
      }),
    );
    await waitFor(() => {
      expect(startGame).toHaveBeenCalledTimes(1);
    });
    await waitFor(() => {
      expect(screen.getByLabelText("対戦モード")).toBeDisabled();
      expect(
        screen.getByRole("button", {
          name: "対局を開始する",
        }),
      ).toBeDisabled();
    });
    expect(screen.getByText("対局中・設定固定")).toBeInTheDocument();
  });

  it("リセット後は対局設定を再び変更できる", async () => {
    const user = userEvent.setup();
    render(<App />);
    await screen.findAllByRole("gridcell");
    await user.click(
      screen.getByRole("button", {
        name: "対局を開始する",
      }),
    );
    await waitFor(() => {
      expect(
        screen.getByRole("button", {
          name: "対局を開始する",
        }),
      ).toBeDisabled();
    });
    await user.click(
      screen.getByRole("button", {
        name: "リセット",
      }),
    );
    await waitFor(() => {
      expect(screen.getByLabelText("対戦モード")).toBeEnabled();
      expect(
        screen.getByRole("button", {
          name: "対局を開始する",
        }),
      ).toBeEnabled();
    });
  });
  it("開始済みの対局では設定変更を禁止する", async () => {
    const startedState: GameState = {
      ...initialState,
      started: true,
    };
    vi.mocked(getGameState).mockResolvedValue(startedState);
    render(<App />);
    await screen.findAllByRole("gridcell");
    expect(screen.getByLabelText("対戦モード")).toBeDisabled();
    expect(screen.getByRole("button", { name: "対局を開始する" })).toBeDisabled();
  });
  it("409エラー発生時に細心の対局状態を取得する", async () => {
    const user = userEvent.setup();
    const latestState: GameState = {
      ...initialState,
      mode: "pvc",
      difficulty: "hard",
      human_color: 1,
      cpu_color: 2,
      started: true,
    };

    vi.mocked(getGameState)
      .mockResolvedValueOnce(initialState)
      .mockResolvedValueOnce(latestState);
    vi.mocked(playHumanMove).mockRejectedValue(
      new ApiError("Game state was updated concurrently", 409),
    );
    render(<App />);
    await screen.findAllByRole("gridcell");
    await user.click(screen.getByRole("button", { name: /3行4列/ }));
    await waitFor(() => {
      expect(getGameState).toHaveBeenCalledTimes(2);
    });
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "最新の盤面を読み込みました",
    );
    expect(screen.getByLabelText("対戦モード")).toBeDisabled();
    expect(screen.getByLabelText("CPUの難易度")).toHaveValue("hard");
  });
  it("初回通信失敗後に再度読み込みできる", async () => {
    const user = userEvent.setup();
    vi.mocked(getGameState)
      .mockRejectedValueOnce(new ApiError("接続できません", 0))
      .mockResolvedValueOnce(initialState);

    render(<App />);

    expect(await screen.findByRole("alert")).toHaveTextContent("接続できません");

    await user.click(screen.getByRole("button", { name: "再度読み込み" }));

    await waitFor(() => {
      expect(screen.getAllByRole("gridcell")).toHaveLength(64);
    });

    expect(getGameState).toHaveBeenCalledTimes(2);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
