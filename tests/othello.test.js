
/**
 * @vitest-environment jsdom
 */

import { beforeEach, afterEach, expect, test, vi } from "vitest";

const initialState = {
    board: Array.from({ length: 8 }, () => Array(8).fill(0)),
    turn: 1,
    message: "",
    mode: "pvp",
    valid_moves: [[2, 3], [3, 2], [4, 5], [5, 4]],
};

beforeEach(async () => {
    vi.resetModules();

    document.body.innerHTML = `
        <div id="board"></div>
        <div id="info"></div>
        <select id="mode">
            <option value="pvp">PvP</option>
            <option value="pvc">PvC</option>
        </select>
        <button id="reset-button">Reset</button>
    `;

    vi.stubGlobal("fetch", vi.fn(async () => ({
        ok: true,
        json: async () => initialState,
    })));

    await import("../static/js/othello.js");
});

afterEach(() => {
    vi.unstubAllGlobals();
});

test("初期表示時にGET /stateを呼び出す", async () => {
    await vi.waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(
            "/state",
            { method: "GET" },
        );
    });
});

test("初期盤面が64マス表示される", async () => {
    await vi.waitFor(() => {
        expect(document.querySelectorAll(".cell")).toHaveLength(64);
    });
});
