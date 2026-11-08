
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    // 旧JavaScriptのテストだけを実行する
    include: ["test_js/**/*.test.js"],

    // Reactフロントエンドのテストは別ジョブに任せる
    exclude: ["node_modules/**", "frontend/**"],
  },
});
