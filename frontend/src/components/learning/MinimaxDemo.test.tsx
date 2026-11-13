import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { MinimaxDemo } from "./MinimaxDemo";

describe("MinimaxDemo", () => {
  it("初期状態では解説を表示する", () => {
    // コンポーネントをテスト環境に描画する
    render(<MinimaxDemo />);

    // まだ候補を選んでいない場合の文言を検証する
    expect(
      screen.getByText("候補を選択すると解説が表示されます。"),
    ).toBeInTheDocument();
  });

  it("候補Aを選択すると正解を表示する", async () => {
    // 実際のユーザー操作を再現する
    const user = userEvent.setup();
    render(<MinimaxDemo />);

    // ラジオボタンの候補Aを選択する
    await user.click(screen.getByRole("radio", { name: "候補A" }));

    // MINはmin(3,5)=3を選び、MAXの正解はA
    expect(screen.getByRole("status")).toHaveTextContent("正解です");
    expect(screen.getByRole("status")).toHaveTextContent("min(3, 5) = 3");
  });

  it("候補Bを選択すると正解の候補Aを説明する", async () => {
    const user = userEvent.setup();
    render(<MinimaxDemo />);

    await user.click(screen.getByRole("radio", { name: "候補B" }));

    // Bはmin(2,9)=2のため、正解はA
    expect(screen.getByRole("status")).toHaveTextContent("min(2, 9) = 2");
    expect(screen.getByRole("status")).toHaveTextContent("候補Aを選ぶべき");
  });

  it("選択したラジオボタンの状態が更新される", async () => {
    const user = userEvent.setup();
    render(<MinimaxDemo />);

    const choiceA = screen.getByRole("radio", { name: "候補A" });
    const choiceB = screen.getByRole("radio", { name: "候補B" });

    await user.click(choiceA);
    expect(choiceA).toBeChecked();

    await user.click(choiceB);
    expect(choiceB).toBeChecked();
    expect(choiceA).not.toBeChecked();
  });
});
