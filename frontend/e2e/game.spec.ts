import { test, expect } from "@playwright/test";

test("対局を開始すると設定が固定される", async ({ page }) => {
  await page.goto("/");

  const startButton = page.getByRole("button", {
    name: "対局を開始する",
  });

  await expect(startButton).toBeEnabled();

  // 実際の画面からPvP対局を開始する
  await startButton.click();

  // APIが開始済み状態を返した後、設定がロックされる
  await expect(startButton).toBeDisabled();
  await expect(page.getByLabel("対戦モード")).toBeDisabled();

  // ページを再読み込みしてもSQLiteの状態が残る
  await page.reload();

  await expect(startButton).toBeDisabled();
  await expect(page.getByText("対局中・設定固定")).toBeVisible();
});

test("着手後の盤面が復元され、リセットで初期化される", async ({ page }) => {
  await page.goto("/");

  // 初期盤面で黒が置ける合法手
  const moveButton = page.getByRole("button", {
    name: "3行4列: 合法手に置く",
  });

  await expect(moveButton).toBeEnabled();
  await moveButton.click();

  // 黒石が置かれたことを確認
  const blackStone = page.getByRole("img", {
    name: "3行4列: 黒石",
  });

  await expect(blackStone).toBeVisible();

  // 再読み込みしても同じ石が残る
  await page.reload();
  await expect(blackStone).toBeVisible();

  // リセットで初期盤面に戻る
  await page.getByRole("button", { name: "リセット" }).click();

  await expect(
    page.getByRole("button", {
      name: "3行4列: 合法手に置く",
    }),
  ).toBeEnabled();

  await expect(page.getByRole("button", { name: "対局を開始する" })).toBeEnabled();
});

test("EasyのCPU対戦で解析結果が表示される", async ({ page }) => {
  await page.goto("/");

  // PvCモード・Easyを選択
  await page.getByLabel("対戦モード").selectOption("pvc");
  await page.getByLabel("CPUの難易度").selectOption("easy");

  await page
    .getByRole("button", {
      name: "対局を開始する",
    })
    .click();

  await expect(
    page.getByRole("button", {
      name: "対局を開始する",
    }),
  ).toBeDisabled();

  // 人間の初手を実行
  await page
    .getByRole("button", {
      name: "3行4列: 合法手に置く",
    })
    .click();

  // FastAPIのCPU解析・着手が終わるまで待つ
  await expect(page.getByText("候補手の比較")).toBeVisible();

  // 着手後は再び人間の手番になる
  await expect(page.getByText("あなたの手番", { exact: true }).first()).toBeVisible();
});
