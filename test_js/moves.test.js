/** @vitest-environment jsdom */

import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import {
  cleanupOthello,
  changeSelect,
  getCell,
  getCpuCalls,
  getMoveCalls,
  mockResponse,
  setupOthello,
  waitForIdle,
} from "./helpers/othello-fixture.js";

beforeEach(async () => {
  await setupOthello();
});

afterEach(() => {
  cleanupOthello();
});

describe("着手", () => {
  test("合法手からPOST /moves/playerを呼び出す", async () => {
    getCell(2, 3).click();

    await vi.waitFor(() => {
      expect(fetch).toHaveBeenCalledWith("/moves/player", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ y: 2, x: 3 }),
      });
    });
  });

  test("合法手以外ではリクエストしない", () => {
    getCell(0, 0).click();

    expect(getMoveCalls()).toHaveLength(0);
  });

  test("着手するとモード切替を無効化する", async () => {
    getCell(2, 3).click();

    await vi.waitFor(() => {
      expect(document.getElementById("mode").disabled).toBe(true);
    });
  });

  test("着手すると難易度選択も無効化する", async () => {
    changeSelect("mode", "pvc");

    await vi.waitFor(() => {
      expect(document.getElementById("difficulty").disabled).toBe(false);
      expect(document.getElementById("reset-button").disabled).toBe(false);
    });

    getCell(2, 3).click();

    await vi.waitFor(() => {
      expect(document.getElementById("difficulty").disabled).toBe(true);
    });
  });

  test("PvPではCPU着手APIを呼び出さない", async () => {
    getCell(2, 3).click();

    await waitForIdle();

    expect(getMoveCalls()).toHaveLength(1);
    expect(getCpuCalls()).toHaveLength(0);
  });
});

describe("PvCの着手とCPU思考表示", () => {
  test("黒石を先に表示してからCPUが着手する", async () => {
    // PvCモードへ変更
    changeSelect("mode", "pvc");

    await vi.waitFor(() => {
      expect(document.getElementById("difficulty").disabled).toBe(false);
      expect(document.getElementById("reset-button").disabled).toBe(false);
    });

    // 通常のfetchモックを保存
    const originalFetch = fetch.getMockImplementation();

    // CPUの応答だけを保留する
    let resolveCpuRequest;

    fetch.mockImplementation((url, options) => {
      if (url === "/moves/cpu") {
        return new Promise((resolve) => {
          resolveCpuRequest = resolve;
        });
      }

      return originalFetch(url, options);
    });

    // 黒石を置く
    getCell(2, 3).click();

    // CPUの応答前に黒石が描画され、思考中表示になることを確認
    await vi.waitFor(() => {
      expect(getCell(2, 3).querySelector(".black")).not.toBeNull();
      expect(document.getElementById("info").textContent).toBe(
        "CPUが考えています…",
      );
    });

    // CPU用APIが呼び出されるまで待つ
    await vi.waitFor(() => {
      expect(getCpuCalls()).toHaveLength(1);
    });

    // CPU応答前には、新しい白石は表示されない
    expect(getCell(2, 4).querySelector(".white")).toBeNull();

    // CPUの応答を返す
    const currentBoard = Array.from(document.querySelectorAll(".cell")).map(
      (cell) =>
        cell.querySelector(".black") ? 1 : cell.querySelector(".white") ? 2 : 0,
    );

    const board = Array.from({ length: 8 }, (_, y) =>
      currentBoard.slice(y * 8, (y + 1) * 8),
    );

    board[2][4] = 2;

    resolveCpuRequest(
      mockResponse({
        board,
        turn: 1,
        mode: "pvc",
        difficulty: "normal",
        message: "",
        valid_moves: [],
      }),
    );

    // CPU応答後に白石が表示される
    await vi.waitFor(() => {
      expect(getCell(2, 4).querySelector(".white")).not.toBeNull();

      expect(document.getElementById("info").textContent).not.toBe(
        "通信エラーが発生しました",
      );
    });

    await waitForIdle();
  });

  test("CPU思考中に追加の着手を送信しない", async () => {
    changeSelect("mode", "pvc");

    await vi.waitFor(() => {
      expect(document.getElementById("difficulty").disabled).toBe(false);
      expect(document.getElementById("reset-button").disabled).toBe(false);
    });

    const baseFetch = fetch.getMockImplementation();
    let resolveCpuRequest;

    fetch.mockImplementation((url, options) => {
      if (url === "/moves/cpu") {
        return new Promise((resolve) => {
          resolveCpuRequest = resolve;
        });
      }

      return baseFetch(url, options);
    });

    getCell(2, 3).click();

    await vi.waitFor(() => {
      expect(getCpuCalls()).toHaveLength(1);
    });

    const before = getMoveCalls().length;

    getCell(2, 3).click();

    expect(getMoveCalls()).toHaveLength(before);
    expect(document.getElementById("reset-button").disabled).toBe(true);

    // CPUによる着手後の正常なゲーム状態を取得する
    // baseFetchはCPUの遅延モックを適用する前のfetch実装
    const response = await baseFetch("/moves/cpu", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: "{}",
    });

    // 保留していたCPUの応答を正常なレスポンスで解決する
    resolveCpuRequest(response);

    // フロントエンドの処理が終了したことを確認する
    await waitForIdle();

    // CPU着手後にエラーが表示されていないことも検証する
    expect(document.getElementById("info").textContent).toContain("黒の番");

    await waitForIdle();
  });
});

describe("二重操作防止", () => {
  test("通信中の連続クリックで重複リクエストしない", async () => {
    let resolveRequest;

    fetch.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveRequest = resolve;
        }),
    );

    const cell = getCell(2, 3);

    cell.click();
    cell.click();

    expect(getMoveCalls()).toHaveLength(1);

    resolveRequest(
      mockResponse({
        board: Array.from({ length: 8 }, () => Array(8).fill(0)),
        turn: 2,
        message: "",
        mode: "pvp",
        difficulty: "normal",
        valid_moves: [],
      }),
    );

    await waitForIdle();
  });
});
