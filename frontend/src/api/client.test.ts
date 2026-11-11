import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ApiError,
  getAnalysis,
  getGameState,
  playCpuMove,
  playHumanMove,
  resetGame,
  startGame,
} from "./client";

import type { GameState } from "@/types/game";

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

// テスト用のHTTPレスポンスを作る
function mockResponse(payload: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: vi.fn().mockResolvedValue(payload),
  };
}

// 各テストで差し替えたfetchを元に戻す
afterEach(() => {
  vi.unstubAllGlobals();
});

describe("API client", () => {
  it("GET /stateでゲーム状態を取得する", async () => {
    const fetchMock = vi.fn().mockResolvedValue(mockResponse(initialState));
    vi.stubGlobal("fetch", fetchMock);

    const state = await getGameState();

    expect(state).toEqual(initialState);

    expect(fetchMock).toHaveBeenCalledWith(
      "/state",
      expect.objectContaining({
        method: "GET",
        credentials: "same-origin",
      }),
    );
  });

  it("対局開始設定をPOSTで送信する", async () => {
    const fetchMock = vi.fn().mockResolvedValue(mockResponse(initialState));
    vi.stubGlobal("fetch", fetchMock);

    const settings = {
      mode: "pvc" as const,
      difficulty: "easy" as const,
      human_order: "random" as const,
    };

    await startGame(settings);

    expect(fetchMock).toHaveBeenCalledWith(
      "/games/start",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(settings),
      }),
    );
  });

  it("人間の着手座標をPOSTする", async () => {
    const fetchMock = vi.fn().mockResolvedValue(mockResponse(initialState));
    vi.stubGlobal("fetch", fetchMock);

    await playHumanMove({ y: 2, x: 3 });

    expect(fetchMock).toHaveBeenCalledWith(
      "/moves/player",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ y: 2, x: 3 }),
      }),
    );
  });

  it("CPU解析トークンをPOSTする", async () => {
    const fetchMock = vi.fn().mockResolvedValue(mockResponse(initialState));
    vi.stubGlobal("fetch", fetchMock);

    await playCpuMove("test-token");

    expect(fetchMock).toHaveBeenCalledWith(
      "/moves/cpu",
      expect.objectContaining({
        body: JSON.stringify({
          analysis_token: "test-token",
        }),
      }),
    );
  });

  it("リセットAPIを呼び出す", async () => {
    const fetchMock = vi.fn().mockResolvedValue(mockResponse(initialState));
    vi.stubGlobal("fetch", fetchMock);

    await resetGame();

    expect(fetchMock).toHaveBeenCalledWith(
      "/reset",
      expect.objectContaining({
        method: "POST",
      }),
    );
  });

  it("HTTPエラーのステータスを保持する", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(mockResponse({ error: "Illegal move" }, 400)),
    );

    await expect(playHumanMove({ y: 0, x: 0 })).rejects.toMatchObject({
      name: "ApiError",
      status: 400,
      message: "Illegal move",
    });
  });

  it("ネットワーク障害をApiErrorに変換する", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    await expect(getGameState()).rejects.toBeInstanceOf(ApiError);

    await expect(getGameState()).rejects.toMatchObject({
      status: 0,
    });
  });

  it("不正なゲーム状態を拒否する", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        mockResponse({
          ...initialState,
          board: [[0, 0]],
        }),
      ),
    );

    await expect(getGameState()).rejects.toMatchObject({
      status: 0,
      message: "ゲーム状態の形式が不正です",
    });
  });

  it("CPU解析結果を取得できる", async () => {
    const analysis = {
      best_move: [2, 4],
      score: 15,
      depth: 1,
      nodes_visited: 10,
      cutoffs: 0,
      elapsed_ms: 2.5,
      candidates: [
        {
          move: [2, 4],
          minimax_score: 17,
          penalty: 1,
          total_score: 15,
        },
      ],
      analysis_token: "test-token",
    };

    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockResponse(analysis)));

    const result = await getAnalysis(1);

    expect(result.best_move).toEqual([2, 4]);
    expect(result.analysis_token).toBe("test-token");
  });
});
