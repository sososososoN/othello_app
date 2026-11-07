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
const cpuContinueButton = document.getElementById("cpu-continue-button");
const cpuExecutionModeElement = document.getElementById("cpu-execution-mode");

// ゲーム中の画面側の状態
let gameStarted = false;
let isLoading = false;
let currentTurn = 1;
let currentMode = "pvp";
let currentDifficulty = "normal";
let pendingCpuTurn = false;

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

  // 解析機能はPvCモードでのみ使用可能
  analysisCheckbox.disabled =
    isLoading || pendingCpuTurn || currentMode !== "pvc";

  // 解析ONのときだけCPU実行方式を選べる
  // CPUの着手待ち中は切り替えを禁止
  cpuExecutionModeElement.disabled =
    isLoading ||
    pendingCpuTurn ||
    currentMode !== "pvc" ||
    !analysisCheckbox.checked;

  updateAnalysisLayout();

  // ステップ実行の待機中のみ進行ボタンを表示
  cpuContinueButton.hidden = !pendingCpuTurn;
  cpuContinueButton.disabled = isLoading;
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
  // CPUの手番以外は何もしない
  if (state.mode !== "pvc" || state.turn !== 2) {
    return;
  }

  infoElement.textContent = "CPUが考えています…";
  await waitForPaint();

  if (analysisCheckbox.checked) {
    try {
      // まず既存の解析APIから候補手の評価を取得
      const analysis = await requestJson("/analysis");

      // 右側の解析結果と盤面上の評価値を描画
      renderAnalysis(analysis);
      await waitForPaint();

      // ステップ実行ならここで処理を終了する
      if (cpuExecutionModeElement.value === "step") {
        pendingCpuTurn = true;
        updateControls();

        infoElement.textContent =
          "解析結果を確認して「次の手へ」を押してください";

        return;
      }

      // 自動実行なら停止せず下のCPU着手処理へ進む
    } catch (error) {
      // 解析失敗時も対局は続行する
      console.error("CPU analysis failed:", error);
      clearAnalysis();
    }
  }

  // 解析OFF・自動実行・解析失敗時のCPU着手
  const cpuState = await requestJson("/moves/cpu", "POST", {});

  // 着手後の盤面を表示
  // 盤面は再生成されるので評価値の重ね表示も消える
  drawBoard(cpuState);
}

async function continueCpuTurn() {
  // 着手待ちでない場合や通信中は何もしない
  if (!pendingCpuTurn || isLoading) return;

  await runRequest(async () => {
    // CPUの着手をAPIに依頼
    const state = await requestJson("/moves/cpu", "POST", {});

    // 正常終了した場合のみ待機状態を解除
    pendingCpuTurn = false;

    // CPU着手後の盤面を表示
    drawBoard(state);

    // ボタンを非表示に戻す
    updateControls();
  });
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
  pendingCpuTurn = false;

  document.querySelectorAll(".analysis-score").forEach((element) => {
    element.remove();
  });

  document.querySelectorAll(".analysis-best").forEach((element) => {
    element.classList.remove("analysis-best");
  });

  analysisContent.replaceChildren();

  updateControls();
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
  paintAnalysisScores(analysis);
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

function paintAnalysisScores(analysis) {
  document.querySelectorAll(".analysis-score").forEach((element) => {
    element.remove();
  });
  document.querySelectorAll(".analysis-best").forEach((element) => {
    element.classList.remove("analysis-best");
  });

  const cells = boardElement.querySelectorAll(".cell");

  for (const candidate of analysis.candidates) {
    const [y, x] = candidate.move;
    const index = y * 8 + x;
    if (
      !Number.isInteger(y) ||
      !Number.isInteger(x) ||
      y < 0 ||
      y >= 8 ||
      x < 0 ||
      x >= 8
    ) {
      continue;
    }
    const cell = cells[index];
    if (!cell || cell.querySelector(".stone")) {
      continue;
    }
    const score = document.createElement("span");
    score.className = "analysis-score";
    score.textContent = String(candidate.total_score);
    const isBest =
      analysis.best_move !== null &&
      y === analysis.best_move[0] &&
      x === analysis.best_move[1];
    if (isBest) {
      cell.classList.add("analysis-best");
      score.setAttribute("aria-label", "CPUの最善手");
    }
    cell.appendChild(score);
  }
}

cpuContinueButton.addEventListener("click", () => {
  void continueCpuTurn();
});

modeElement.addEventListener("change", () => {
  void changeMode();
});

analysisCheckbox.addEventListener("change", () => {
  clearAnalysis();
});

difficultyElement.addEventListener("change", () => {
  void changeDifficulty();
});

// イベントを登録する
resetButton.addEventListener("click", () => {
  void resetGame();
});

void initializeGame();
