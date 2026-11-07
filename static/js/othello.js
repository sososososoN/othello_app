"use strict";

// HTML要素を取得する
const boardElement = document.getElementById("board");
const infoElement = document.getElementById("info");
const modeElement = document.getElementById("mode");
const resetButton = document.getElementById("reset-button");
const difficultyElement = document.getElementById("difficulty");
const analysisCheckbox = document.getElementById("analysis-enabled");
const analysisPanel = document.getElementById("analysis-panel");
const analysisContent = document.getElementById("analysis-content");
const gameLayout = document.getElementById("game-layout");

// ゲーム中の画面側の状態
let gameStarted = false;
let isLoading = false;
let currentTurn = 1;
let currentMode = "pvp";
let currentDifficulty = "normal";

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
    throw new Error(`APIエラー: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

// API通信中に操作が重複しないようにする
async function runRequest(task) {
  if (isLoading) return false;

  isLoading = true;
  updateControls();
  resetButton.disabled = true;

  try {
    await task();
    return true;
  } catch (error) {
    console.error(error);
    infoElement.textContent = "通信エラーが発生しました";
    return false;
  } finally {
    isLoading = false;
    updateControls();
    resetButton.disabled = false;
  }
}

function updateControls() {
  modeElement.disabled = gameStarted;
  difficultyElement.disabled = gameStarted || currentMode !== "pvc";
  difficultyElement.value = currentDifficulty;
  analysisCheckbox.disabled = isLoading || currentMode !== "pvc";

  updateAnalysisLayout();
}

function drawBoard(state) {
  boardElement.replaceChildren();

  modeElement.value = state.mode;

  currentTurn = state.turn;
  currentMode = state.mode;
  currentDifficulty = state.difficulty ?? "normal";

  updateControls();

  if (state.turn === 0) {
    infoElement.textContent = state.message || "ゲーム終了";
  } else {
    const turnText = state.turn === 1 ? "黒の番" : "白の番";
    infoElement.textContent = state.message
      ? `${turnText} (${state.message})`
      : turnText;
  }

  // CPUの番では合法手のヒントを非表示にする
  const isCpuTurn = state.mode === "pvc" && state.turn === 2;

  const showHints = state.turn !== 0 && !isCpuTurn;

  // 合法手をSetに変換して検索しやすくする
  const validMoves = new Set(
    showHints ? (state.valid_moves || []).map(([y, x]) => `${y},${x}`) : [],
  );

  state.board.forEach((row, y) => {
    row.forEach((cell, x) => {
      const square = document.createElement("div");
      square.className = "cell";

      const isValid = validMoves.has(`${y},${x}`);

      if (cell !== 0) {
        const stone = document.createElement("div");
        stone.className = `stone ${cell === 1 ? "black" : "white"}`;
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

function waitForPaint() {
  return new Promise((resolve) => {
    requestAnimationFrame(() => {
      requestAnimationFrame(resolve);
    });
  });
}

async function finishCpuTurn(state) {
  if (state.mode !== "pvc" || state.turn !== 2) return;

  infoElement.textContent = "CPUが考えています…";
  await waitForPaint();
  if (analysisCheckbox.checked) {
    try {
      const analysis = await requestJson("/analysis?depth=1");
      renderAnalysis(analysis);
      await waitForPaint();
    } catch (error) {
      console.error("CPU analysis failed", error);
      clearAnalysis();
    }
  }

  const cpuState = await requestJson("/moves/cpu", "POST", {});
  drawBoard(cpuState);
}

async function sendMove(y, x) {
  if (isLoading || currentTurn === 0) return;

  await runRequest(async () => {
    clearAnalysis();
    const state = await requestJson("/moves/player", "POST", { y, x });
    gameStarted = true;
    drawBoard(state);
    await finishCpuTurn(state);
  });
}

// 新しいゲームを開始する
async function resetGame() {
  await runRequest(async () => {
    clearAnalysis();
    const state = await requestJson("/reset", "POST", {});

    gameStarted = false;
    drawBoard(state);
  });
}

// ページ初期表示時に現在の盤面を取得する
async function initializeGame() {
  await runRequest(async () => {
    const state = await requestJson("/state");
    const stoneCount = state.board.flat().filter((cell) => cell !== 0).length;

    gameStarted = stoneCount > 4 || state.turn === 0;
    drawBoard(state);

    await finishCpuTurn(state);
  });
}

async function changeMode() {
  if (isLoading || gameStarted) {
    modeElement.value = currentMode;
    return;
  }

  const selectedMode = modeElement.value;

  const success = await runRequest(async () => {
    const state = await requestJson("/mode", "PATCH", { mode: selectedMode });

    drawBoard(state);
  });
  if (!success) {
    modeElement.value = currentMode;
  }
}

async function changeDifficulty() {
  if (isLoading || gameStarted || currentMode !== "pvc") {
    difficultyElement.value = currentDifficulty;
    return;
  }

  const selectedDifficulty = difficultyElement.value;

  const success = await runRequest(async () => {
    const state = await requestJson("/difficulty", "PATCH", {
      difficulty: selectedDifficulty,
    });

    drawBoard(state);
  });

  if (!success) {
    difficultyElement.value = currentDifficulty;
  }
}

function clearAnalysis() {
  analysisContent.replaceChildren();
  updateAnalysisLayout();
}

function renderAnalysis(analysis) {
  analysisContent.replaceChildren();
  const summary = document.createElement("p");
  summary.textContent =
    `探索深さ: ${analysis.depth} / ` +
    `探索ノード: ${analysis.nodes_visited} / ` +
    `枝刈り: ${analysis.cutoffs}`;

  analysisContent.appendChild(summary);
  const candidates = [...analysis.candidates].sort(
    (a, b) => b.total_score - a.total_score,
  );
  const list = document.createElement("ol");

  for (const candidate of candidates) {
    const item = document.createElement("li");
    const [y, x] = candidate.move;

    const isBest =
      analysis.best_move !== null &&
      y === analysis.best_move[0] &&
      x === analysis.best_move[1];
    item.textContent =
      `(${y}, ${x}) 評価値: ${candidate.total_score}` +
      (isBest ? " 【最善手】" : "");
    list.appendChild(item);
  }

  analysisContent.appendChild(list);
  analysisPanel.hidden = false;
}

function updateAnalysisLayout() {
  // PvCモードかつチェックONの場合に解析を表示する
  const enabled = currentMode === "pvc" && analysisCheckbox.checked;

  // CSSの2カラムレイアウトを切り替える
  gameLayout.classList.toggle("analysis-on", enabled);

  // 解析パネルの表示状態を同期する
  analysisPanel.hidden = !enabled;

  // チェック直後、まだ解析結果がない場合の案内
  if (enabled && analysisContent.textContent.trim() === "") {
    analysisContent.textContent =
      "CPUが着手すると、ここに解析結果を表示します。";
  }
}

modeElement.addEventListener("change", () => {
  void changeMode();
});

analysisCheckbox.addEventListener("change", () => {
  clearAnalysis();
  updateAnalysisLayout();
});

difficultyElement.addEventListener("change", () => {
  void changeDifficulty();
});

// イベントを登録する
resetButton.addEventListener("click", () => {
  void resetGame();
});

void initializeGame();
