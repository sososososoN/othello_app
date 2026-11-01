# Othello AI Lab

オセロを通じて、AIの探索アルゴリズムを学べるWebアプリケーションです。

FastAPIとJavaScriptを使用して開発しています。通常のオセロ対戦に加え、Minimax法などのアルゴリズムを解説コラムやインタラクティブなデモで学習できるサイトを目指しています。

## 主な機能

### オセロ対戦

- PvP（対人戦）・PvC（CPU対戦）
- Minimax法とαβ枝刈りによるCPU
- Easy / Normal / Hardの難易度選択
- 合法手の表示、パス・勝敗判定
- CPU思考中の表示
- SQLiteによる対局状態の保存・再開

### アルゴリズム学習

- 学習コラム一覧
- Minimax法の解説記事
- インタラクティブな探索木デモ

今後、CPUの探索過程の可視化やアルゴリズム比較機能を追加する予定です。

## 技術スタック

| 分野 | 技術 |
|---|---|
| Backend | Python 3.13 / FastAPI / Pydantic |
| Frontend | HTML / CSS / JavaScript / Jinja2 |
| Database | SQLite |
| Content | Markdown |
| Testing | pytest / Vitest |
| Lint / Format | Ruff / ESLint / Prettier |
| CI | GitHub Actions |
| Container | Docker / Docker Compose |

## セットアップ

### 1. リポジトリを取得

```bash
git clone https://github.com/sososososoN/othello_app.git
cd othello_app
```

### 2. Python環境を準備

Python 3.13を使用します。

Windows PowerShell：

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 3. JavaScriptの依存関係をインストール

Node.jsとnpmが必要です。

```powershell
npm ci
```

### 4. 環境変数を設定

プロジェクト直下に `.env` を作成します。

```dotenv
SESSION_SECRET_KEY=your-random-secret-key
OTHELLO_DB_PATH=data/othello.db
```

署名鍵は以下のコマンドで生成できます。

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

生成した値を `SESSION_SECRET_KEY` に設定してください。

`.env` はGit管理対象外です。

## 起動方法

### ローカル実行

```powershell
python -m uvicorn app:app --reload --port 5001 --env-file .env
```

### Docker

Docker DesktopなどのDocker実行環境と、必要な環境変数を設定した `.env` を用意してください。

```powershell
docker compose up --build -d
```

停止：

```powershell
docker compose down
```

SQLiteのデータはDocker Volumeに永続化されます。

## アクセス先

ローカル起動時：

| ページ | URL |
|---|---|
| オセロ対戦 | http://127.0.0.1:5001/ |
| 学習コラム一覧 | http://127.0.0.1:5001/learn |
| Minimax法の解説 | http://127.0.0.1:5001/learn/minimax |
| APIドキュメント | http://127.0.0.1:5001/docs |

## プロジェクト構成

主要ディレクトリ・ファイルのみ記載します。

```text
othello_app/
├── app.py              # FastAPI
├── game.py             # オセロのルール
├── cpu.py              # CPUの探索アルゴリズム
├── service.py          # ゲーム操作
├── storage.py          # SQLiteによる状態管理
├── schemas.py          # APIスキーマ
├── learning/           # 学習記事の管理
├── content/algorithms/ # Markdown形式の学習記事
├── templates/          # HTMLテンプレート
├── static/             # CSS・JavaScript
├── tests/              # Pythonテスト
├── test_js/            # JavaScriptテスト
├── Dockerfile
├── compose.yaml
└── requirements.txt
```

## 開発・テスト

### Python

```powershell
python -m ruff check .
python -m ruff format --check .
python -m pytest -v
```

### JavaScript

```powershell
npm run lint
npm run format:check
npm test
```

GitHub ActionsでCIを実行しています。

開発は作業ブランチを作成し、Pull Request経由で `main` に反映する方針です。

## 今後の予定

- AI探索エンジンのモジュール分割
- CPUの候補手・評価値・探索ノード数の可視化
- Minimax法・αβ枝刈りなどの学習コラム拡充
- 探索木のインタラクティブな可視化
- アルゴリズム比較・実験機能
- 本番環境へのデプロイ

## 注意事項

- 現在のゲーム状態管理は単一サーバープロセスでの利用を想定しています。
- 学習用Minimaxデモは固定データを使用しており、実際のCPU探索とは未連携です。
- CPUの応答時間は探索深さや盤面によって変化します。

## ライセンス

[MIT License](LICENSE)