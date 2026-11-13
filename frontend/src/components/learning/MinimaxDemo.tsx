import { useState } from "react";

// 候補ごとに相手（MIN）が選べる評価値を定義
const tree = {
  A: [3, 5],
  B: [2, 9],
} as const;

type Choice = keyof typeof tree;

function evaluateMinimax(scores: readonly number[]): number {
  // MINは最も小さい評価値を選択する
  return Math.min(...scores);
}

export function MinimaxDemo() {
  // nullはまだ候補が選択されていない状態
  const [choice, setChoice] = useState<Choice | null>(null);

  const bestChoice: Choice = "A";
  const selectedScores = choice === null ? null : tree[choice];

  const explanation =
    choice === null || selectedScores === null
      ? "候補を選択すると解説が表示されます。"
      : `候補${choice}の評価値は min(${selectedScores.join(", ")}) = ${evaluateMinimax(selectedScores)}。` +
        `相手は評価値を最小化します。` +
        (choice === bestChoice
          ? ` 正解です。MAXは候補${bestChoice}を選びます。`
          : ` MAXは評価値3の候補${bestChoice}を選ぶべきです。`);

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Minimaxを体験する</h2>

      <p className="text-sm leading-7 text-muted-foreground">
        MAXはどちらの候補を選ぶべきでしょうか。
        相手のMINは、それぞれの候補で最小値を選びます。
      </p>

      <div aria-label="Minimaxの探索木" className="space-y-5 text-center">
        <div className="mx-auto w-fit rounded-sm bg-primary px-6 py-2 text-primary-foreground">
          MAX
        </div>

        <div className="grid grid-cols-2 gap-3">
          {(["A", "B"] as const).map((candidate) => (
            <div key={candidate} className="space-y-3">
              <div className="rounded-sm border border-border bg-muted px-3 py-2 font-medium">
                候補{candidate} / MIN
              </div>
              <div className="flex justify-center gap-3">
                {tree[candidate].map((score) => (
                  <span key={score} className="min-w-10 border border-border px-3 py-2">
                    {score}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <fieldset className="space-y-3">
        <legend className="font-medium">MAXはどちらを選ぶべきでしょうか？</legend>

        {(["A", "B"] as const).map((candidate) => (
          <label
            key={candidate}
            className="mr-6 inline-flex cursor-pointer items-center gap-2"
          >
            <input
              type="radio"
              name="minimax-choice"
              value={candidate}
              checked={choice === candidate}
              onChange={() => setChoice(candidate)}
              className="accent-primary"
            />
            候補{candidate}
          </label>
        ))}
      </fieldset>

      <div
        role="status"
        aria-live="polite"
        className="border-l-2 border-primary bg-muted px-4 py-3 text-sm leading-7"
      >
        {explanation}
      </div>
    </div>
  );
}
