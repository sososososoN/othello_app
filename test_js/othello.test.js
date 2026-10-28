
/** @vitest-environment jsdom */

import {
    afterEach,
    beforeEach,
    describe,
    expect,
    test,
    vi,
} from "vitest";

function createState(overrides = {}) {
    const board = Array.from(
        { length: 8 },
        () => Array(8).fill(0)
    );

    board[3][3] = 2;
    board[3][4] = 1;
    board[4][3] = 1;
    board[4][4] = 2;

    return {
        board,
        turn: 1,
        message: "",
        mode: "pvp",
        valid_moves: [
            [2, 3],
            [3, 2],
            [4, 5],
            [5, 4],
        ],
        ...overrides,
    };
}

function mockResponse(state) {
    return {
        ok: true,
        status: 200,
        statusText: "OK",
        json: async () => state,
    };
}

function getCell(y, x) {
    const cells = document.querySelectorAll(".cell");
    return cells[y * 8 + x];
}

function getMoveCalls() {
    return fetch.mock.calls.filter(
        ([url]) => url === "/moves"
    );
}

async function waitForBoard() {
    await vi.waitFor(() => {
        expect(document.querySelectorAll(".cell"))
            .toHaveLength(64);

        expect(
            document.getElementById("reset-button").disabled
        ).toBe(false);
    });
}

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

    vi.stubGlobal(
        "fetch",
        vi.fn(async (url) => {
            if (url === "/mode") {
                return mockResponse(
                    createState({ mode: "pvc" })
                );
            }

            if (url === "/moves") {
                return mockResponse(
                    createState({ turn: 2 })
                );
            }

            return mockResponse(createState());
        })
    );

    await import("../static/js/othello.js");
    await waitForBoard();
});

afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
});

describe("初期表示", () => {
    test("GET /stateを呼び出す", () => {
        expect(fetch).toHaveBeenCalledWith(
            "/state",
            { method: "GET" }
        );
    });

    test("盤面は64マス", () => {
        expect(
            document.querySelectorAll(".cell")
        ).toHaveLength(64);
    });

    test("初期状態の石は4つ", () => {
        expect(
            document.querySelectorAll(".stone")
        ).toHaveLength(4);
    });

    test("合法手のヒントは4つ", () => {
        expect(
            document.querySelectorAll(".hint")
        ).toHaveLength(4);
    });

    test("合法手以外にヒントを表示しない", () => {
        expect(
            getCell(2, 3).querySelector(".hint")
        ).not.toBeNull();

        expect(
            getCell(0, 0).querySelector(".hint")
        ).toBeNull();
    });

    test("初期状態では黒の番と表示する", () => {
        expect(
            document.getElementById("info").textContent
        ).toContain("黒の番");
    });
});

describe("着手", () => {
    test("合法手からPOST /movesを呼び出す", async () => {
        getCell(2, 3).click();

        await vi.waitFor(() => {
            expect(fetch).toHaveBeenCalledWith(
                "/moves",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        y: 2,
                        x: 3,
                    }),
                }
            );
        });
    });

    test("合法手以外ではリクエストしない", () => {
        getCell(0, 0).click();

        expect(getMoveCalls()).toHaveLength(0);
    });

    test("着手するとモード切替を無効化する", async () => {
        getCell(2, 3).click();

        await vi.waitFor(() => {
            expect(
                document.getElementById("mode").disabled
            ).toBe(true);
        });
    });
});

describe("リセット", () => {
    test("POST /resetを呼び出す", async () => {
        document.getElementById("reset-button").click();

        await vi.waitFor(() => {
            expect(fetch).toHaveBeenCalledWith(
                "/reset",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: "{}",
                }
            );
        });
    });

    test("リセット後にモード切替を再び有効化する", async () => {
        getCell(2, 3).click();

        await vi.waitFor(() => {
            expect(
                document.getElementById("mode").disabled
            ).toBe(true);
        });

        document.getElementById("reset-button").click();

        await vi.waitFor(() => {
            expect(
                document.getElementById("mode").disabled
            ).toBe(false);

            expect(
                document.querySelectorAll(".hint")
            ).toHaveLength(4);
        });
    });
});

describe("モード切替", () => {
    test("PvC選択時にPATCH /modeを呼び出す", async () => {
        const mode = document.getElementById("mode");

        mode.value = "pvc";
        mode.dispatchEvent(new Event("change"));

        await vi.waitFor(() => {
            expect(fetch).toHaveBeenCalledWith(
                "/mode",
                {
                    method: "PATCH",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        mode: "pvc",
                    }),
                }
            );
        });

        expect(mode.value).toBe("pvc");
    });

    test("ゲーム開始後にはモード変更しない", async () => {
        getCell(2, 3).click();

        await vi.waitFor(() => {
            expect(
                document.getElementById("mode").disabled
            ).toBe(true);
        });

        const mode = document.getElementById("mode");

        mode.value = "pvc";
        mode.dispatchEvent(new Event("change"));

        expect(mode.value).toBe("pvp");

        const modeCalls = fetch.mock.calls.filter(
            ([url]) => url === "/mode"
        );

        expect(modeCalls).toHaveLength(0);
    });
});

describe("通信エラー", () => {
    test("着手失敗時にエラーメッセージを表示する", async () => {
        vi.spyOn(console, "error")
            .mockImplementation(() => {});

        fetch.mockRejectedValueOnce(
            new Error("Network error")
        );

        getCell(2, 3).click();

        await vi.waitFor(() => {
            expect(
                document.getElementById("info").textContent
            ).toBe("通信エラーが発生しました");
        });
    });

    test("モード変更失敗時は元の選択に戻す", async () => {
        vi.spyOn(console, "error")
            .mockImplementation(() => {});

        fetch.mockRejectedValueOnce(
            new Error("Network error")
        );

        const mode = document.getElementById("mode");
        mode.value = "pvc";
        mode.dispatchEvent(new Event("change"));

        await vi.waitFor(() => {
            expect(mode.value).toBe("pvp");
            expect(
                document.getElementById("info").textContent
            ).toBe("通信エラーが発生しました");
        });
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
                })
            );
        });

        document.getElementById("reset-button").click();

        await vi.waitFor(() => {
            expect(
                document.getElementById("info").textContent
            ).toBe("ゲーム終了");
        });

        expect(
            document.querySelectorAll(".hint")
        ).toHaveLength(0);
    });

    test("CPUの手番にはヒントを表示しない", async () => {
        fetch.mockImplementationOnce(async () => {
            return mockResponse(
                createState({
                    mode: "pvc",
                    turn: 2,
                })
            );
        });

        document.getElementById("reset-button").click();

        await vi.waitFor(() => {
            expect(
                document.getElementById("mode").value
            ).toBe("pvc");

            expect(
                document.getElementById("info").textContent
            ).toContain("白の番");
        });

        expect(
            document.querySelectorAll(".hint")
        ).toHaveLength(0);
    });
});

describe("二重操作防止", () => {
    test("通信中の連続クリックで重複リクエストしない", async () => {
        let resolveRequest;

        fetch.mockImplementationOnce(
            () => new Promise((resolve) => {
                resolveRequest = resolve;
            })
        );

        const cell = getCell(2, 3);

        cell.click();
        cell.click();

        expect(getMoveCalls()).toHaveLength(1);

        resolveRequest(
            mockResponse(createState({ turn: 2 }))
        );

        await vi.waitFor(() => {
            expect(
                document.getElementById("reset-button").disabled
            ).toBe(false);
        });
    });
});
