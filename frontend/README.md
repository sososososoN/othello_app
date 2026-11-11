# Othello AI Lab — Frontend

React・TypeScript・Viteを使用したOthello AI Labのフロントエンドです。

プロジェクト全体のセットアップ、バックエンド起動、Docker、API仕様については[ルートのREADME](../README.md)を参照してください。

## 開発コマンド

`frontend/`ディレクトリで実行します。

```powershell
npm ci
npm run dev
```

開発サーバーは通常`http://127.0.0.1:5173/`で利用します。ゲームAPIを使用するには、別途FastAPIを5001番ポートで起動してください。

## テスト・品質チェック

```powershell
npm run lint
npm run format:check
npm test
npm run build
```

## 主要ディレクトリ

- `src/api/`：FastAPIとの通信・レスポンス検証
- `src/components/game/`：ゲーム盤面とCPU解析パネル
- `src/components/layout/`：画面全体のレイアウト
- `src/components/ui/`：共通UIコンポーネント
- `src/types/`：ゲーム関連のTypeScript型定義
- `src/App.tsx`：ゲーム画面と状態管理

本番用の配信ファイルは`npm run build`で`dist/`に生成されます。
