/** @vitest-environment jsdom */

import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import {
  changeSelect,
  cleanupOthello,
  getCalls,
  getCell,
  setupOthello,
  waitForIdle,
} from "./helpers/othello-fixture.js";

let server;

beforeEach(async () => {
  server = await setupOthello();
});

afterEach(() => {
  cleanupOthello();
});

describe("リセット", () => {
  test("POST /resetを呼び出す", async () => {
    document.getElementById("reset-button").click();

    await vi.waitFor(() => {
      expect(fetch).toHaveBeenCalledWith("/reset", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: "{}",
      });
    });
  });

  test("リセット後にモード切替を再び有効化する", async () => {
    getCell(2, 3).click();

    await vi.waitFor(() => {
      expect(document.getElementById("mode").disabled).toBe(true);
    });

    await waitForIdle();

    document.getElementById("reset-button").click();

    await vi.waitFor(() => {
      expect(document.getElementById("mode").disabled).toBe(false);
      expect(document.querySelectorAll(".hint")).toHaveLength(4);
    });
  });

  test("リセット後も選択した難易度を維持する", async () => {
    changeSelect("mode", "pvc");

    await vi.waitFor(() => {
      expect(document.getElementById("difficulty").disabled).toBe(false);
      expect(document.getElementById("reset-button").disabled).toBe(false);
    });

    changeSelect("difficulty", "hard");

    await vi.waitFor(() => {
      expect(server.getState().difficulty).toBe("hard");
      expect(document.getElementById("difficulty").value).toBe("hard");
      expect(document.getElementById("reset-button").disabled).toBe(false);
    });

    document.getElementById("reset-button").click();

    await vi.waitFor(() => {
      expect(getCalls("/reset")).toHaveLength(1);
      expect(document.getElementById("difficulty").value).toBe("hard");
      expect(document.getElementById("difficulty").disabled).toBe(false);
    });
  });
});

describe("モード切替", () => {
  test("PvC選択時にPATCH /modeを呼び出す", async () => {
    const mode = changeSelect("mode", "pvc");

    await vi.waitFor(() => {
      expect(fetch).toHaveBeenCalledWith("/mode", {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ mode: "pvc" }),
      });
    });

    expect(mode.value).toBe("pvc");
  });

  test("PvCに変更すると難易度選択が有効になる", async () => {
    changeSelect("mode", "pvc");

    await vi.waitFor(() => {
      expect(document.getElementById("difficulty").disabled).toBe(false);
    });
  });

  test("PvPに戻すと難易度選択が無効になる", async () => {
    changeSelect("mode", "pvc");

    await vi.waitFor(() => {
      expect(document.getElementById("difficulty").disabled).toBe(false);
      expect(document.getElementById("reset-button").disabled).toBe(false);
    });

    const mode = changeSelect("mode", "pvp");

    await vi.waitFor(() => {
      expect(mode.value).toBe("pvp");
      expect(document.getElementById("difficulty").disabled).toBe(true);
    });
  });

  test("ゲーム開始後にはモード変更しない", async () => {
    getCell(2, 3).click();

    await vi.waitFor(() => {
      expect(document.getElementById("mode").disabled).toBe(true);
    });

    const mode = changeSelect("mode", "pvc");

    expect(mode.value).toBe("pvp");
    expect(getCalls("/mode")).toHaveLength(0);
  });
});

describe("CPU難易度", () => {
  test.each(["easy", "normal", "hard"])(
    "%sをPATCH /difficultyで設定できる",
    async (selectedDifficulty) => {
      changeSelect("mode", "pvc");

      await vi.waitFor(() => {
        expect(document.getElementById("difficulty").disabled).toBe(false);
        expect(document.getElementById("reset-button").disabled).toBe(false);
      });

      changeSelect("difficulty", selectedDifficulty);

      await vi.waitFor(() => {
        expect(fetch).toHaveBeenCalledWith("/difficulty", {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ difficulty: selectedDifficulty }),
        });

        expect(server.getState().difficulty).toBe(selectedDifficulty);
      });
    },
  );

  test("PvPでは難易度を変更できない", () => {
    const difficulty = changeSelect("difficulty", "hard");

    expect(difficulty.value).toBe("normal");
    expect(getCalls("/difficulty")).toHaveLength(0);
  });

  test("ゲーム開始後は難易度変更APIを呼ばない", async () => {
    changeSelect("mode", "pvc");

    await vi.waitFor(() => {
      expect(document.getElementById("difficulty").disabled).toBe(false);
      expect(document.getElementById("reset-button").disabled).toBe(false);
    });

    getCell(2, 3).click();

    await vi.waitFor(() => {
      expect(document.getElementById("difficulty").disabled).toBe(true);
    });

    const difficulty = changeSelect("difficulty", "hard");

    expect(difficulty.value).toBe("normal");
    expect(getCalls("/difficulty")).toHaveLength(0);
  });

  test("難易度変更失敗時は元の値に戻す", async () => {
    changeSelect("mode", "pvc");

    await vi.waitFor(() => {
      expect(document.getElementById("difficulty").disabled).toBe(false);
      expect(document.getElementById("reset-button").disabled).toBe(false);
    });

    vi.spyOn(console, "error").mockImplementation(() => {});

    fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
    });

    const difficulty = changeSelect("difficulty", "hard");

    await vi.waitFor(() => {
      expect(getCalls("/difficulty")).toHaveLength(1);
      expect(difficulty.value).toBe("normal");
      expect(document.getElementById("info").textContent).toBe(
        "通信エラーが発生しました",
      );
    });
  });
});
