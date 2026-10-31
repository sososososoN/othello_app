/** @vitest-environment jsdom */

import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import {
  cleanupOthello,
  createState,
  getCell,
  mockResponse,
  setupOthello,
} from "./helpers/othello-fixture.js";

beforeEach(async () => {
  await setupOthello();
});

afterEach(() => {
  cleanupOthello();
});

describe("初期表示", () => {
  test("GET /stateを呼び出す", () => {
    expect(fetch).toHaveBeenCalledWith("/state", {
      method: "GET",
    });
  });

  test("盤面は64マス", () => {
    expect(document.querySelectorAll(".cell")).toHaveLength(64);
  });

  test("初期状態の石は4つ", () => {
    expect(document.querySelectorAll(".stone")).toHaveLength(4);
  });

  test("合法手のヒントは4つ", () => {
    expect(document.querySelectorAll(".hint")).toHaveLength(4);
  });

  test("合法手以外にヒントを表示しない", () => {
    expect(getCell(2, 3).querySelector(".hint")).not.toBeNull();

    expect(getCell(0, 0).querySelector(".hint")).toBeNull();
  });

  test("初期状態では黒の番と表示する", () => {
    expect(document.getElementById("info").textContent).toContain("黒の番");
  });

  test("初期状態はPvP・Normal", () => {
    expect(document.getElementById("mode").value).toBe("pvp");

    expect(document.getElementById("difficulty").value).toBe("normal");
  });

  test("PvPでは難易度選択を無効化する", () => {
    expect(document.getElementById("difficulty").disabled).toBe(true);
  });
});

describe("ゲーム状態", () => {
  test("ゲーム終了時にはヒントを表示しない", async () => {
    fetch.mockImplementationOnce(async () => {
      return mockResponse(
        createState({
          turn: 0,
          message: "ゲーム終了",
          valid_moves: [],
        }),
      );
    });

    document.getElementById("reset-button").click();

    await vi.waitFor(() => {
      expect(document.getElementById("info").textContent).toBe("ゲーム終了");
    });

    expect(document.querySelectorAll(".hint")).toHaveLength(0);
  });

  test("CPUの手番にはヒントを表示しない", async () => {
    fetch.mockImplementationOnce(async () => {
      return mockResponse(
        createState({
          mode: "pvc",
          turn: 2,
        }),
      );
    });

    document.getElementById("reset-button").click();

    await vi.waitFor(() => {
      expect(document.getElementById("mode").value).toBe("pvc");
      expect(document.getElementById("info").textContent).toContain("白の番");
    });

    expect(document.querySelectorAll(".hint")).toHaveLength(0);
  });
});
