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
  const sortedCandidates = [...analysis.candidates].sort(
    (a, b) => b.total_score - a.total_score,
  );
  return (
    <Card>
      <CardHeader>
        <CardTitle>CPUの思考解析</CardTitle>
        <CardDescription>直前のCPUの手に使用した解析結果</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-md bg-muted p-3">
            <p className="text-xs text-muted-foreground">最善手</p>
            <p className="text-lg font-semibold">
              {analysis.best_move ? formatPosition(analysis.best_move) : "なし"}
            </p>
          </div>
          <div className="rounded-md bg-muted p-3">
            <p className="text-xs text-muted-foreground">評価値</p>
            <p className="text-lg font-semibold">
              {analysis.score === null ? "-" : formatScore(analysis.score)}
            </p>
          </div>
          <div className="rounded-md bg-muted p-3">
            <p className="text-xs text-muted-foreground">探索ノード数</p>
            <p className="text-lg font-semibold">
              {analysis.nodes_visited.toLocaleString()}
            </p>
          </div>
          <div className="rounded-md bg-muted p-3">
            <p className="text-xs text-muted-foreground">解析時間</p>
            <p className="text-lg font-semibold">{analysis.elapsed_ms.toFixed(1)} ms</p>
          </div>
          <p className="text-sm text-muted-foreground">
            探索深さ: {analysis.depth}/ 枝刈り回数: {analysis.cutoffs}
          </p>
          <div className="space-y-2">
            <h3 className="text-sm font-semibold">候補手の比較</h3>
            {sortedCandidates.length === 0 ? (
              <p className="text-sm text-muted-foreground">候補手はありません。</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b">
                      <th scope="col" className="p-2">
                        候補手
                      </th>
                      <th scope="col" className="p-2 text-right">
                        評価値
                      </th>
                      <th scope="col" className="p-2 text-right">
                        ペナルティ
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedCandidates.map((candidate) => {
                      const isBest =
                        analysis.best_move !== null &&
                        candidate.move[0] === analysis.best_move[0] &&
                        candidate.move[1] === analysis.best_move[1];

                      return (
                        <tr
                          key={candidate.move.join("-")}
                          className={
                            isBest ? "bg-primary/10 font-semibold" : "border-b"
                          }
                        >
                          <td className="p-2">
                            {formatPosition(candidate.move)}
                            {isBest && "（最善手）"}
                          </td>

                          <td className="p-2 text-right">
                            {formatScore(candidate.total_score)}
                          </td>

                          <td className="p-2 text-right">{candidate.penalty}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
          <p className="text-xs text-muted-foreground">
            評価値はCPU内部の比較指標です。 石数差や勝率を直接表すものではありません。
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
