/** @vitest-environment jsdom */

import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import {
  changeSelect,
  cleanupOthello,
  getCell,
  setupOthello,
} from "./helpers/othello-fixture.js";

beforeEach(async () => {
  await setupOthello();
});

afterEach(() => {
  cleanupOthello();
});

describe("通信エラー", () => {
  test("着手失敗時にエラーメッセージを表示する", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});

    fetch.mockRejectedValueOnce(new Error("Network error"));

    getCell(2, 3).click();

    await vi.waitFor(() => {
      expect(document.getElementById("info").textContent).toBe(
        "通信エラーが発生しました",
      );
    });
  });

  test("モード変更失敗時は元の選択に戻す", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});

    fetch.mockRejectedValueOnce(new Error("Network error"));

    const mode = changeSelect("mode", "pvc");

    await vi.waitFor(() => {
      expect(mode.value).toBe("pvp");
      expect(document.getElementById("info").textContent).toBe(
        "通信エラーが発生しました",
      );
    });
  });
});
