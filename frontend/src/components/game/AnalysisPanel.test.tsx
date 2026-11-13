import { describe, expect, it } from "vitest";
import { render, screen, within } from "@testing-library/react";

import { AnalysisPanel } from "./AnalysisPanel";
import type { AnalysisResult } from "@/types/game";

// テスト用の解析結果
const analysis: AnalysisResult = {
  best_move: [2, 2],
  score: 12,
  depth: 1,
  nodes_visited: 25,
  cutoffs: 3,
  elapsed_ms: 4.5,
  candidates: [
    {
      move: [2, 4],
      minimax_score: 10,
      penalty: 1,
      total_score: 8,
    },
    {
      move: [2, 2],
      minimax_score: 16,
      penalty: 2,
      total_score: 12,
    },
  ],
  analysis_token: "test-token",
};

describe("AnalysisPanel", () => {
  it("解析の概要を表示する", () => {
    render(<AnalysisPanel analysis={analysis} />);
    const table = screen.getByRole("table");
    expect(screen.getByText("CPUの思考解析")).toBeInTheDocument();
    expect(screen.getAllByText("C3", { exact: true })).toHaveLength(2);
    expect(within(table).getByText("+12")).toBeInTheDocument();
    expect(screen.getByText("25")).toBeInTheDocument();
    expect(screen.getByText("4.5 ms")).toBeInTheDocument();
  });

  it("候補手を評価値の高い順に並べる", () => {
    render(<AnalysisPanel analysis={analysis} />);

    const table = screen.getByRole("table");
    const rows = within(table).getAllByRole("row");

    // 1行目はヘッダー、2行目が最善手
    expect(within(rows[1]).getByText(/C3/)).toBeInTheDocument();
    expect(within(rows[2]).getByText("E3")).toBeInTheDocument();
  });

  it("候補手がない場合にメッセージを表示する", () => {
    render(
      <AnalysisPanel
        analysis={{
          ...analysis,
          best_move: null,
          score: null,
          candidates: [],
        }}
      />,
    );

    expect(screen.getByText("候補手はありません。")).toBeInTheDocument();
  });

  it("最善手に最善ラベルを付ける", () => {
    render(<AnalysisPanel analysis={analysis} />);

    const table = screen.getByRole("table");
    const rows = within(table).getAllByRole("row");

    expect(within(rows[1]).getByText("C3")).toBeInTheDocument();
    expect(within(rows[1]).getByText("最善")).toBeInTheDocument();
    expect(within(rows[2]).getByText("E3")).toBeInTheDocument();
  });
});
