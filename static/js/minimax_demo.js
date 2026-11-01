"use strict";

// MINは各候補から最も小さい評価値を選ぶ
const tree = {
  A: [3, 5],
  B: [2, 9],
};

function evaluateMinimax(options) {
  return Math.min(...options);
}

function getBestChoice() {
  return Object.entries(tree).reduce(
    (best, [choice, scores]) => {
      const score = evaluateMinimax(scores);
      return score > best.score ? { choice, score } : best;
    },
    { choice: null, score: -Infinity },
  );
}

function initializeMinimaxDemo() {
  const result = document.getElementById("minimax-result");
  const choices = document.querySelectorAll('input[name="minimax-choice"]');

  if (!result || choices.length === 0) {
    return;
  }

  const best = getBestChoice();

  for (const input of choices) {
    input.addEventListener("change", () => {
      if (!input.checked) {
        return;
      }

      const choice = input.value;
      const scores = tree[choice];

      if (!scores) {
        return;
      }

      const score = evaluateMinimax(scores);
      const correct = choice === best.choice;

      const explanation =
        `候補${choice}の評価値は min(${scores.join(", ")}) = ${score}。` +
        `相手は評価値を最小化します。` +
        (correct
          ? ` 正解です。MAXは候補${best.choice}を選びます。`
          : ` MAXは評価値${best.score}の候補${best.choice}を選ぶべきです。`);

      result.textContent = explanation;
      result.dataset.correct = String(correct);
    });
  }
}

initializeMinimaxDemo();
