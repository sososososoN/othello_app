import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import type { AnalysisResult, Position } from "@/types/game";

function formatPosition([y, x]: Position): string {
  const column = String.fromCharCode(65 + x);
  return `${column}${y + 1}`;
}

function formatScore(score: number): string {
  return score > 0 ? `+${score}` : String(score);
}

type AnalysisPanelProps = {
  analysis: AnalysisResult;
};

export function AnalysisPanel({ analysis }: AnalysisPanelProps) {
  // 変更：元の配列を変更せず評価値の降順に並べる
  const sortedCandidates = [...analysis.candidates].sort(
    (a, b) => b.total_score - a.total_score,
  );

  return (
    <Card className="min-w-0">
      <CardHeader>
        <CardTitle>CPUの思考解析</CardTitle>
        <CardDescription>直前のCPUの手に使用した解析結果</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-2 gap-x-6 gap-y-5 border-y border-border py-5">
          <div>
            <p className="text-xs text-muted-foreground">最善手</p>
            <p className="mt-1 text-2xl font-semibold tracking-tight">
              {analysis.best_move ? formatPosition(analysis.best_move) : "なし"}
            </p>
          </div>

          <div>
            <p className="text-xs text-muted-foreground">評価値</p>
            <p className="mt-1 text-2xl font-semibold tracking-tight tabular-nums">
              {analysis.score === null ? "—" : formatScore(analysis.score)}
            </p>
          </div>

          <div>
            <p className="text-xs text-muted-foreground">探索ノード数</p>
            <p className="mt-1 text-xl font-semibold tabular-nums">
              {analysis.nodes_visited.toLocaleString()}
            </p>
          </div>

          <div>
            <p className="text-xs text-muted-foreground">解析時間</p>
            <p className="mt-1 text-xl font-semibold tabular-nums">
              {analysis.elapsed_ms.toFixed(1)} ms
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-x-6 gap-y-2 text-xs text-muted-foreground">
          <span>探索深さ：{analysis.depth}</span>
          <span>枝刈り回数：{analysis.cutoffs}</span>
        </div>

        {/* 変更：候補手の表に横幅を確保 */}
        <section className="min-w-0 space-y-3">
          <div className="flex items-center justify-between gap-3">
            <h3 className="text-sm font-semibold">候補手の比較</h3>
            <span className="text-xs text-muted-foreground">
              {sortedCandidates.length}候補
            </span>
          </div>

          {sortedCandidates.length === 0 ? (
            <p className="rounded-lg border border-dashed border-border p-5 text-sm text-muted-foreground">
              候補手はありません。
            </p>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-border">
              <table className="w-full min-w-[320px] border-collapse text-sm">
                <thead className="bg-muted/70 text-muted-foreground">
                  <tr>
                    <th scope="col" className="w-12 px-3 py-3 text-center font-medium">
                      順位
                    </th>
                    <th scope="col" className="px-3 py-3 text-left font-medium">
                      候補手
                    </th>
                    <th scope="col" className="px-3 py-3 text-right font-medium">
                      評価値
                    </th>
                    <th scope="col" className="px-3 py-3 text-right font-medium">
                      ペナルティ
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {sortedCandidates.map((candidate, index) => {
                    const isBest =
                      analysis.best_move !== null &&
                      candidate.move[0] === analysis.best_move[0] &&
                      candidate.move[1] === analysis.best_move[1];

                    return (
                      <tr
                        key={candidate.move.join("-")}
                        className={
                          isBest
                            ? "border-t border-border bg-primary/10"
                            : "border-t border-border even:bg-muted/25"
                        }
                      >
                        <td className="px-3 py-3 text-center text-muted-foreground tabular-nums">
                          {index + 1}
                        </td>

                        <td className="px-3 py-3">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-semibold">
                              {formatPosition(candidate.move)}
                            </span>

                            {isBest && (
                              <span className="text-xs font-medium text-primary">
                                最善
                              </span>
                            )}
                          </div>
                        </td>

                        <td className="px-3 py-3 text-right font-semibold tabular-nums">
                          {formatScore(candidate.total_score)}
                        </td>

                        <td className="px-3 py-3 text-right text-muted-foreground tabular-nums">
                          {candidate.penalty}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <p className="border-t border-border pt-4 text-xs leading-relaxed text-muted-foreground">
          評価値はCPU内部の比較指標です。 石数差や勝率を直接表すものではありません。
        </p>
      </CardContent>
    </Card>
  );
}
