# Othello AI Lab

オセロをプレイしながら、Minimax法やαβ枝刈りなどのAI探索アルゴリズムを学べるWebアプリケーションです。

フロントエンドはReact・TypeScript、バックエンドはFastAPI・Pythonで構成されています。対局状態はSQLiteに保存され、CPUが選んだ手の評価値や探索統計を確認できます。

## 主な機能

### オセロ対戦

- PvP（2人対戦）とPvC（CPU対戦）
- Easy / Normal / Hardの難易度選択
- CPU対戦での先攻・後攻・ランダム選択
- 合法手の表示、石の反転、パス・終局判定
- 対局設定、盤面、CPU解析パネルのReact UI
- SQLiteによる対局状態の保存と再読み込み時の復元

### CPUの思考解析

- Minimax法とαβ枝刈りによる着手選択
- 最善手・候補手ごとの評価値とペナルティの表示
- 探索深さ、探索ノード数、枝刈り回数、解析時間の表示
- 署名付き解析トークンを使った解析結果の着手への再利用

CPU解析は、PvCモードでCPUの手番のときに利用できます。

### アルゴリズム学習

- 学習コラムの一覧
- Markdown形式のMinimax法解説記事
- 固定された探索木を使ったインタラクティブなMinimaxデモ

学習ページは現在、ReactではなくFastAPI・Jinja2で配信しています。

## 技術スタック

| 分野 | 使用技術 |
|---|---|
| Frontend | React / TypeScript / Vite |
| UI | Tailwind CSS / shadcn/ui系コンポーネント |
| Backend | Python 3.13 / FastAPI / Pydantic |
| AI | Minimax法 / αβ枝刈り |
| Database | SQLite |
| 学習コンテンツ | Markdown / Jinja2 |
| Frontendテスト | Vitest / React Testing Library |
| Backendテスト | pytest |
| Lint・整形 | Oxlint / Prettier / Ruff |
| CI | GitHub Actions |
| コンテナ | Docker / Docker Compose |

## ディレクトリ構成

```text
othello_app/
├── backend/
│   ├── ai/
│   │   ├── analysis_token.py   # 解析結果の署名と検証
│   │   ├── engine.py           # CPUの着手選択・解析
│   │   ├── evaluation.py       # 局面評価関数
│   │   ├── models.py           # 解析結果と探索統計の型
│   │   └── search.py           # Minimax・αβ枝刈り
│   ├── learning/
│   │   └── articles.py         # 学習記事の管理
│   ├── app.py                  # FastAPIルーティング
│   ├── game.py                 # オセロのルール
│   ├── schemas.py              # API入出力スキーマ
│   ├── service.py              # 対局操作・状態遷移
│   └── storage.py              # SQLiteへの保存・読み込み
├── frontend/
│   ├── public/                 # 画像など
│   ├── src/
│   │   ├── api/                # FastAPIへのHTTP通信
│   │   ├── components/         # Reactコンポーネント
│   │   ├── lib/                # 共通ユーティリティ
│   │   ├── test/               # テスト共通設定
│   │   ├── types/              # TypeScript型定義
│   │   ├── App.tsx             # オセロ画面
│   │   └── main.tsx            # React起動処理
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── vitest.config.ts
├── content/algorithms/         # 学習記事のMarkdown
├── static/                     # 学習ページ用CSS・JavaScript
├── templates/                  # 学習ページ用Jinja2テンプレート
├── tests/                      # Pythonテスト
├── .github/workflows/ci.yaml   # GitHub Actions
├── benchmark_cpu.py            # CPU探索の計測
├── compose.yaml
├── Dockerfile
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

`frontend/dist/` はViteのビルド時に生成されるディレクトリです。Gitには登録しません。

## ローカルセットアップ

Windows PowerShellでのセットアップ例です。

### 1. リポジトリを取得

```powershell
git clone https://github.com/sososososoN/othello_app.git
cd othello_app
```

### 2. Python環境を作成

Python 3.13を使用します。

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

### 3. 環境変数を設定

プロジェクトのルートに`.env`を作成します。

```powershell
Copy-Item .env.example .env
```

署名鍵を生成します。

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

生成した文字列を`.env`の`SESSION_SECRET_KEY`に設定してください。

```dotenv
SESSION_SECRET_KEY=ここに生成したランダム文字列を設定
OTHELLO_DB_PATH=data/othello.db
```

`SESSION_SECRET_KEY`には32文字以上の鍵が必要です。`.env`はGitにコミットしないでください。

### 4. Reactの依存関係をインストール

Node.jsとnpmを用意し、`frontend/`で実行します。

```powershell
cd frontend
npm ci
cd ..
```

## 起動方法

### 方法A：開発モード（推奨）

FastAPIとViteを別々のターミナルで起動します。

**ターミナル1：FastAPI**

リポジトリのルートから実行します。

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.app:app --reload --port 5001 --env-file .env
```

**ターミナル2：React**

```powershell
cd frontend
npm run dev
```

ブラウザで次のURLにアクセスします。

- React開発画面：`http://127.0.0.1:5173/`
- FastAPIドキュメント：`http://127.0.0.1:5001/docs`

ViteはゲームAPIへのリクエストをFastAPIの5001番ポートに転送します。

### 方法B：FastAPIからReactを配信

Viteの開発サーバーを使わず、Reactのビルド成果物をFastAPIから配信します。

**最初にReactをビルド**

```powershell
cd frontend
npm run build
cd ..
```

**FastAPIを起動**

```powershell
python -m uvicorn backend.app:app --reload --port 5001 --env-file .env
```

アクセス先：`http://127.0.0.1:5001/`

Reactのコードを変更した場合は、再度`npm run build`する必要があります。

ビルド済みファイルが存在しない場合、トップページはHTTP 503を返します。

### 方法C：Docker Compose

Docker Desktopなどの実行環境と`.env`を用意してください。

```powershell
docker compose up --build -d
```

Docker内でReactをビルドし、FastAPIから配信します。

アクセス先：`http://127.0.0.1:5001/`

状態確認：

```powershell
docker compose ps
docker compose logs -f web
```

停止：

```powershell
docker compose down
```

SQLiteデータはDocker Volumeに保存されるため、通常のコンテナ再作成では維持されます。

## 主なURL

| URL | 内容 |
|---|---|
| `/` | オセロ画面（React本番ビルド） |
| `/learn` | 学習コラム一覧 |
| `/learn/minimax` | Minimax法の解説とデモ |
| `/docs` | FastAPIのSwagger UI |
| `/openapi.json` | OpenAPI仕様 |

### 主なゲームAPI

| メソッド | パス | 機能 |
|---|---|---|
| GET | `/state` | 現在の対局状態を取得 |
| POST | `/games/start` | 対戦モード・難易度・先後を指定して対局開始 |
| POST | `/moves/player` | 人間の着手 |
| GET | `/analysis` | CPUの手を解析 |
| POST | `/moves/cpu` | CPUの着手 |
| POST | `/reset` | 盤面をリセット |
| PATCH | `/mode` | 対戦モードの変更 |
| PATCH | `/difficulty` | CPU難易度の変更 |

`POST /moves`も互換用の対局APIとして利用できます。最新のReact画面では、主に`/moves/player`と`/moves/cpu`を使用しています。

`GET /analysis`の`depth`は0〜5を指定できます。省略すると選択されたCPU難易度に応じた探索深さを使用します。

リクエスト・レスポンスの詳細は`/docs`を参照してください。

## テスト・コード品質

### Backend

リポジトリのルートで実行します。

```powershell
python -m ruff check .
python -m ruff format --check .
python -m pytest -v
```

### Frontend

`frontend/`で実行します。

```powershell
cd frontend

npm run lint
npm run format:check
npm test
npm run build
```

整形を適用するときは次を実行します。

```powershell
npm run format
```

GitHub Actionsでは、PythonのLint・テストと、ReactのLint・テスト・ビルドを別のジョブで実行しています。

## 開発上の注意事項

- ゲーム状態はSQLiteに保存されます。
- 同時更新の競合はバージョン番号による楽観的ロックで検出し、HTTP 409を返します。
- 現在のReact画面では、対局開始状態の一部をブラウザの`sessionStorage`でも管理しています。複数タブ間の状態同期は今後の改善対象です。
- CPUの探索時間は難易度と局面によって変化します。
- 学習ページのMinimaxデモは固定データを使用し、実際のCPU探索とは連動していません。
- 本番公開に際しては、HTTPS、セッションCookie設定、CPU解析の負荷対策などを追加で検討してください。

## 今後の予定

- 対局開始状態のバックエンドへの一本化
- API競合時の再同期とエラー復旧の改善
- CPU解析の負荷制限とセキュリティ対策
- ブラウザを使ったE2Eテストの導入
- 探索過程の可視化・アルゴリズム比較機能の拡充

## ライセンス

[MIT License](LICENSE)
