import { test, expect } from "@playwright/test";

test.describe("React学習ページ", () => {
  test("学習一覧から記事へ移動できる", async ({ page }) => {
    // Reactで作られた学習一覧を開く
    await page.goto("/learn");

    // 学習一覧の見出しを確認
    await expect(
      page.getByRole("heading", { name: "アルゴリズムを学ぶ" }),
    ).toBeVisible();

    // 記事リンクをクリックする
    await page.getByRole("link", { name: /Minimax法とは？/ }).click();

    // URLと記事本文が正しいことを確認
    await expect(page).toHaveURL(/\/learn\/minimax$/);
    await expect(page.getByRole("heading", { name: "Minimax法とは？" })).toBeVisible();

    await expect(page.getByRole("heading", { name: "MAXとMIN" })).toBeVisible();
  });

  test("記事の直接アクセスと再読み込みができる", async ({ page }) => {
    // 一覧を経由せず記事URLを直接開く
    await page.goto("/learn/minimax");

    await expect(page.getByRole("heading", { name: "Minimax法とは？" })).toBeVisible();

    // SPA移行で特に壊れやすい再読み込みを確認
    await page.reload();

    await expect(page.getByRole("heading", { name: "Minimax法とは？" })).toBeVisible();

    // 記事一覧へ戻れることも確認
    await page.getByRole("link", { name: /記事一覧へ戻る/ }).click();

    await expect(page).toHaveURL(/\/learn$/);
  });

  test("Minimaxデモで正解と不正解を判定できる", async ({ page }) => {
    await page.goto("/learn/minimax");

    const result = page.getByRole("status");

    // 初期状態
    await expect(result).toContainText("候補を選択すると解説が表示されます。");

    // 候補Bは不正解
    await page.getByRole("radio", { name: "候補B" }).check();

    await expect(result).toContainText("min(2, 9) = 2");
    await expect(result).toContainText("候補Aを選ぶべき");

    // 候補Aは正解
    await page.getByRole("radio", { name: "候補A" }).check();

    await expect(result).toContainText("min(3, 5) = 3");
    await expect(result).toContainText("正解です");
  });

  test("存在しない記事ではエラーメッセージを表示する", async ({ page }) => {
    await page.goto("/learn/unknown");

    await expect(
      page.getByRole("heading", { name: "記事が見つかりません" }),
    ).toBeVisible();

    await page.getByRole("link", { name: "記事一覧へ戻る" }).click();

    await expect(page).toHaveURL(/\/learn$/);
  });
});
