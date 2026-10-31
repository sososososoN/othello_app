
/** @vitest-environment jsdom */

import {
    afterEach,
    beforeEach,
    describe,
    expect,
    test,
    vi,
} from "vitest";

// 8×8の初期盤面とAPIレスポンスを作成する
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
        difficulty: "normal",
        valid_moves: [
            [2, 3],
            [3, 2],
            [4, 5],
            [5, 4],
        ],
        ...overrides,
    };
}

// APIの正常レスポンスを模擬する
function mockResponse(state) {
    return {
        ok: true,
        status: 200,
        statusText: "OK",
        json: async () => state,
    };
}

// APIのエラーレスポンスを模擬する
function mockErrorResponse(status = 500) {
    return {
        ok: false,
        status,
        statusText: "Internal Server Error",
        json: async () => ({
            error: "Internal Server Error",
        }),
    };
}

// 盤面の指定座標に対応するHTML要素を返す
function getCell(y, x) {
    const cells = document.querySelectorAll(".cell");
    return cells[y * 8 + x];
}

// 特定エンドポイントへのリクエストだけ抽出する
function getCalls(url) {
    return fetch.mock.calls.filter(
        ([requestedUrl]) => requestedUrl === url
    );
}

function getMoveCalls() {
    return getCalls("/moves");
}

// 非同期の初期描画が完了するまで待つ
async function waitForBoard() {
    await vi.waitFor(() => {
        expect(document.querySelectorAll(".cell"))
            .toHaveLength(64);

        expect(
            document.getElementById("reset-button").disabled
        ).toBe(false);
    });
}

let serverState;

beforeEach(async () => {
    vi.resetModules();

    document.body.innerHTML = `
        <div id="board"></div>
        <div id="info"></div>

        <select id="mode">
            <option value="pvp">PvP</option>
            <option value="pvc">PvC</option>
        </select>

        <select id="difficulty" disabled>
            <option value="easy">Easy</option>
            <option value="normal">Normal</option>
            <option value="hard">Hard</option>
        </select>

        <button id="reset-button">Reset</button>
    `;

    serverState = createState();

    // サーバー側に状態が保持されている状況を模擬する
    vi.stubGlobal(
        "fetch",
        vi.fn(async (url, options = {}) => {
            const method = options.method ?? "GET";

            if (url === "/state" && method === "GET") {
                return mockResponse(serverState);
            }

            if (url === "/mode" && method === "PATCH") {
                const body = JSON.parse(options.body);

                serverState = {
                    ...serverState,
                    mode: body.mode,
                };

                return mockResponse(serverState);
            }

            if (
                url === "/difficulty" &&
                method === "PATCH"
            ) {
                const body = JSON.parse(options.body);

                serverState = {
                    ...serverState,
                    difficulty: body.difficulty,
                };

                return mockResponse(serverState);
            }

            if (url === "/moves" && method === "POST") {
                const body = JSON.parse(options.body);

                const board = serverState.board.map(
                    (row) => row.slice()
                );

                board[body.y][body.x] = 1;

                serverState = {
                    ...serverState,
                    board,
                    turn: 2,
                    valid_moves: [],
                };

                return mockResponse(serverState);
            }

            if (url === "/reset" && method === "POST") {
                serverState = createState({
                    mode: serverState.mode,
                    difficulty: serverState.difficulty,
                });

                return mockResponse(serverState);
            }

            throw new Error(
                `Unexpected request: ${method} ${url}`
            );
        })
    );

    // 各テストでJSの状態変数とイベント登録を初期化する
    await import("../static/js/othello.js");
    await waitForBoard();
});

afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    document.body.innerHTML = "";
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

    test("初期状態はPvP・Normal", () => {
        expect(
            document.getElementById("mode").value
        ).toBe("pvp");

        expect(
            document.getElementById("difficulty").value
        ).toBe("normal");
    });

    test("PvPでは難易度選択を無効化する", () => {
        expect(
            document.getElementById("difficulty").disabled
        ).toBe(true);
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

    test("着手すると難易度選択も無効化する", async () => {
        const mode = document.getElementById("mode");
        mode.value = "pvc";
        mode.dispatchEvent(new Event("change"));

        await vi.waitFor(() => {
            expect(
                document.getElementById("difficulty").disabled
            ).toBe(false);
        });

        getCell(2, 3).click();

        await vi.waitFor(() => {
            expect(
                document.getElementById("difficulty").disabled
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
    
test("リセット後も選択した難易度を維持する", async () => {
    const mode = document.getElementById("mode");

    mode.value = "pvc";
    mode.dispatchEvent(new Event("change"));

    // モード変更の通信が終わるまで待つ
    await vi.waitFor(() => {
        expect(
            document.getElementById("difficulty").disabled
        ).toBe(false);
        expect(
            document.getElementById("reset-button").disabled
        ).toBe(false);
    });

    const difficulty = document.getElementById("difficulty");

    difficulty.value = "hard";
    difficulty.dispatchEvent(new Event("change"));

    // 難易度変更の通信・描画がすべて終わるまで待つ
    await vi.waitFor(() => {
        expect(serverState.difficulty).toBe("hard");
        expect(difficulty.value).toBe("hard");
        expect(
            document.getElementById("reset-button").disabled
        ).toBe(false);
    });

    // 通信中でないことを確認してからリセット
    document.getElementById("reset-button").click();

    await vi.waitFor(() => {
        expect(getCalls("/reset")).toHaveLength(1);
        expect(difficulty.value).toBe("hard");
        expect(difficulty.disabled).toBe(false);
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

    test("PvCに変更すると難易度選択が有効になる", async () => {
        const mode = document.getElementById("mode");

        mode.value = "pvc";
        mode.dispatchEvent(new Event("change"));

        await vi.waitFor(() => {
            expect(
                document.getElementById("difficulty").disabled
            ).toBe(false);
        });
    });

    test("PvPに戻すと難易度選択が無効になる", async () => {
        const mode = document.getElementById("mode");

        mode.value = "pvc";
        mode.dispatchEvent(new Event("change"));

        await vi.waitFor(() => {
            expect(
                document.getElementById("difficulty").disabled
            ).toBe(false);
        });

        mode.value = "pvp";
        mode.dispatchEvent(new Event("change"));

        await vi.waitFor(() => {
            expect(mode.value).toBe("pvp");
            expect(
                document.getElementById("difficulty").disabled
            ).toBe(true);
        });
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
        expect(getCalls("/mode")).toHaveLength(0);
    });
});

describe("CPU難易度", () => {
    test.each(["easy", "normal", "hard"])(
        "%sをPATCH /difficultyで設定できる",
        async (selectedDifficulty) => {
            const mode = document.getElementById("mode");
            mode.value = "pvc";
            mode.dispatchEvent(new Event("change"));

            await vi.waitFor(() => {
                expect(
                    document.getElementById("difficulty").disabled
                ).toBe(false);
            });

            const difficulty =
                document.getElementById("difficulty");

            difficulty.value = selectedDifficulty;
            difficulty.dispatchEvent(new Event("change"));

            await vi.waitFor(() => {
                expect(fetch).toHaveBeenCalledWith(
                    "/difficulty",
                    {
                        method: "PATCH",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({
                            difficulty: selectedDifficulty,
                        }),
                    }
                );
                expect(serverState.difficulty)
                    .toBe(selectedDifficulty);
            });
        }
    );

    test("PvPでは難易度を変更できない", () => {
        const difficulty =
            document.getElementById("difficulty");

        difficulty.value = "hard";
        difficulty.dispatchEvent(new Event("change"));

        expect(difficulty.value).toBe("normal");
        expect(getCalls("/difficulty")).toHaveLength(0);
    });

    test("ゲーム開始後は難易度変更APIを呼ばない", async () => {
        const mode = document.getElementById("mode");
        mode.value = "pvc";
        mode.dispatchEvent(new Event("change"));

        await vi.waitFor(() => {
            expect(
                document.getElementById("difficulty").disabled
            ).toBe(false);
        });

        getCell(2, 3).click();

        await vi.waitFor(() => {
            expect(
                document.getElementById("difficulty").disabled
            ).toBe(true);
        });

        const difficulty =
            document.getElementById("difficulty");

        difficulty.value = "hard";
        difficulty.dispatchEvent(new Event("change"));

        expect(difficulty.value).toBe("normal");
        expect(getCalls("/difficulty")).toHaveLength(0);
    });

    test("難易度変更失敗時は元の値に戻す", async () => {
        const mode = document.getElementById("mode");

        mode.value = "pvc";
        mode.dispatchEvent(new Event("change"));

        await vi.waitFor(() => {
            expect(
                document.getElementById("difficulty").disabled
            ).toBe(false);
        });

        vi.spyOn(console, "error")
            .mockImplementation(() => {});

        // 次のfetch呼び出しだけエラーにする
        fetch.mockResolvedValueOnce(mockErrorResponse(500));

        const difficulty =
            document.getElementById("difficulty");

        difficulty.value = "hard";
        difficulty.dispatchEvent(new Event("change"));

        await vi.waitFor(() => {
            expect(getCalls("/difficulty")).toHaveLength(1);
            expect(difficulty.value).toBe("normal");

            expect(
                document.getElementById("info").textContent
            ).toBe("通信エラーが発生しました");
        });
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
