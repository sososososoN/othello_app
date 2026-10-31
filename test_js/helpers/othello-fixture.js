import { expect, vi } from "vitest";

// テスト対象のフロントエンドJS
const APP_MODULE = "../../static/js/othello.js";

// 8×8の初期盤面とAPIレスポンスを生成する
export function createState(overrides = {}) {
  const board = Array.from({ length: 8 }, () => Array(8).fill(0));

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

// 正常なAPIレスポンスを模擬する
export function mockResponse(state) {
  return {
    ok: true,
    status: 200,
    statusText: "OK",
    json: async () => state,
  };
}

// APIのエラーレスポンスを模擬する
export function mockErrorResponse(status = 500) {
  return {
    ok: false,
    status,
    statusText: "Internal Server Error",
    json: async () => ({
      error: "Internal Server Error",
    }),
  };
}

// 指定座標のマスを取得する
export function getCell(y, x) {
  const cells = document.querySelectorAll(".cell");
  return cells[y * 8 + x];
}

// 指定したAPIへのリクエストだけを取得する
export function getCalls(url) {
  return fetch.mock.calls.filter(([requestedUrl]) => requestedUrl === url);
}

// 人間の着手APIへのリクエストを取得する
export function getMoveCalls() {
  return getCalls("/moves/player");
}

// CPU着手APIへのリクエストを取得する
export function getCpuCalls() {
  return getCalls("/moves/cpu");
}

// 非同期の画面描画が完了するまで待つ
export async function waitForBoard() {
  await vi.waitFor(() => {
    expect(document.querySelectorAll(".cell")).toHaveLength(64);
    expect(document.getElementById("reset-button").disabled).toBe(false);
  });
}

// 通信処理の終了を待つ
export async function waitForIdle() {
  await vi.waitFor(() => {
    expect(document.getElementById("reset-button").disabled).toBe(false);
  });
}

// セレクトボックスの値を変更してchangeイベントを発火する
export function changeSelect(id, value) {
  const element = document.getElementById(id);
  element.value = value;
  element.dispatchEvent(new Event("change"));
  return element;
}

// テスト用DOMを生成する
function createTestDOM() {
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
}

// 各テストに独立したサーバー状態を用意する
function createMockServer(initialState) {
  let serverState = initialState;

  const fetchMock = vi.fn(async (url, options = {}) => {
    const method = options.method ?? "GET";

    // ゲーム状態の取得
    if (url === "/state" && method === "GET") {
      return mockResponse(serverState);
    }

    // PvP・PvCモードの変更
    if (url === "/mode" && method === "PATCH") {
      const body = JSON.parse(options.body);

      serverState = {
        ...serverState,
        mode: body.mode,
      };

      return mockResponse(serverState);
    }

    // CPU難易度の変更
    if (url === "/difficulty" && method === "PATCH") {
      const body = JSON.parse(options.body);

      serverState = {
        ...serverState,
        difficulty: body.difficulty,
      };

      return mockResponse(serverState);
    }

    // 人間の着手
    if (url === "/moves/player" && method === "POST") {
      const body = JSON.parse(options.body);
      const board = serverState.board.map((row) => row.slice());

      board[body.y][body.x] = 1;

      serverState = {
        ...serverState,
        board,
        turn: 2,
        valid_moves: [],
      };

      return mockResponse(serverState);
    }

    // CPUの着手
    if (url === "/moves/cpu" && method === "POST") {
      const board = serverState.board.map((row) => row.slice());

      board[2][4] = 2;

      serverState = {
        ...serverState,
        board,
        turn: 1,
        valid_moves: [],
      };

      return mockResponse(serverState);
    }

    // ゲームのリセット
    if (url === "/reset" && method === "POST") {
      serverState = createState({
        mode: serverState.mode,
        difficulty: serverState.difficulty,
      });

      return mockResponse(serverState);
    }

    // 想定していないAPI呼び出しはテスト失敗につなげる
    throw new Error(`Unexpected request: ${method} ${url}`);
  });

  return {
    fetchMock,

    getState() {
      return serverState;
    },

    setState(nextState) {
      serverState = nextState;
    },
  };
}

// beforeEachから呼び出す共通セットアップ
export async function setupOthello(initialState = createState()) {
  // ES Moduleのキャッシュを初期化し、イベント登録の重複を防止
  vi.resetModules();

  createTestDOM();

  const server = createMockServer(initialState);

  vi.stubGlobal("fetch", server.fetchMock);

  // jsdomでrequestAnimationFrameを模擬する
  vi.stubGlobal(
    "requestAnimationFrame",
    vi.fn((callback) => setTimeout(callback, 0)),
  );

  // 実際のフロントエンドコードを読み込む
  await import(APP_MODULE);

  // 初期表示の完了を確認する
  await waitForBoard();

  return server;
}

// afterEachから呼び出す共通クリーンアップ
export function cleanupOthello() {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  vi.clearAllTimers();
  document.body.innerHTML = "";
}
