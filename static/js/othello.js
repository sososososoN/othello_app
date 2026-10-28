
"use strict";

// HTML要素を取得する
const boardElement = document.getElementById("board");
const infoElement = document.getElementById("info");
const modeElement = document.getElementById("mode");
const resetButton = document.getElementById("reset-button");

// ゲーム中の画面側の状態
let gameStarted = false;
let isLoading = false;
let currentTurn = 1;
let currentMode = "pvp";

async function requestJson(url, method = "GET", body = null) {
    const options = { method };

    if (body !== null) {
        options.headers = {
            "Content-Type": "application/json",
        };

        options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);

    if (!response.ok) {
        throw new Error(
            `APIエラー: ${response.status} ${response.statusText}`
        );
    }

    return response.json();
}


// API通信中に操作が重複しないようにする
async function runRequest(task) {
    if (isLoading) return false;

    isLoading = true;
    resetButton.disabled = true;

    try {
        await task();
        return true
    } catch (error) {
        console.error(error);
        infoElement.textContent = "通信エラーが発生しました";
        return false;
    } finally {
        isLoading = false;
        resetButton.disabled = false;
    }
}

// Flaskから受け取った盤面を描画する
function drawBoard(state) {
    boardElement.replaceChildren();

    modeElement.value = state.mode;
    currentTurn = state.turn;
    currentMode = state.mode;

    if (state.turn === 0) {
        infoElement.textContent = state.message || "ゲーム終了";
    } else {
        const turnText = state.turn === 1 ? "黒の番" : "白の番";
        infoElement.textContent = state.message
            ? `${turnText} (${state.message})`
            : turnText;
    }

    // CPUの番では合法手のヒントを非表示にする
    const isCpuTurn =
        state.mode === "pvc" && state.turn === 2;

    const showHints = state.turn !== 0 && !isCpuTurn;

    // 合法手をSetに変換して検索しやすくする
    const validMoves = new Set(
        showHints
            ? (state.valid_moves || []).map(
                ([y, x]) => `${y},${x}`
            )
            : []
    );

    state.board.forEach((row, y) => {
        row.forEach((cell, x) => {
            const square = document.createElement("div");
            square.className = "cell";

            const isValid = validMoves.has(`${y},${x}`);

            if (cell !== 0) {
                const stone = document.createElement("div");
                stone.className =
                    `stone ${cell === 1 ? "black" : "white"}`;
                square.appendChild(stone);
            } else if (isValid) {
                const hint = document.createElement("div");
                hint.className = "hint";
                square.appendChild(hint);
            }

            // 合法手以外はクリックさせない
            square.style.cursor = isValid ? "pointer" : "default";

            if (isValid) {
                square.addEventListener("click", () => {
                    void sendMove(y, x);
                });
            }

            boardElement.appendChild(square);
        });
    });
}


async function sendMove(y, x) {
    if (isLoading || currentTurn === 0) return;

    await runRequest(async () => {
        const state = await requestJson(
            "/moves",
            "POST",
            { y, x }
        );

        gameStarted = true;
        modeElement.disabled = true;

        drawBoard(state);
    });
}


// 新しいゲームを開始する
async function resetGame() {
    await runRequest(async () => {
        const state = await requestJson("/reset", "POST", {});

        gameStarted = false;
        modeElement.disabled = false;
        drawBoard(state);
    });
}

// ページ初期表示時に現在の盤面を取得する
async function initializeGame() {
    await runRequest(async () => {
        const state = await requestJson("/state");
        modeElement.value = state.mode;
        const stoneCount = state.board
            .flat()
            .filter((cell) => cell !== 0)
            .length;

        gameStarted = stoneCount > 4 || state.turn === 0;
        modeElement.disabled = gameStarted;

        drawBoard(state);
    });
}


async function changeMode() {
    if (isLoading || gameStarted) {
        modeElement.value = currentMode;
        return;
    }

    const selectMode = modeElement.value;

    const success = await runRequest(async () => {
        const state = await requestJson(
            "/mode",
            "PATCH",
            { mode: selectedMode }
        );

        drawBoard(state);
    });
    if (!success) {
        modeElement.value = currentMode;
    }
}

modeElement.addEventListener("change", () => {
    void changeMode();
});

// イベントを登録する
resetButton.addEventListener("click", () => {
    void resetGame();
});

void initializeGame();
