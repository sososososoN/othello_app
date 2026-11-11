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
- SQLiteによる対局状態と開始済みフラグの保存
- ブラウザ再読み込み時の対局状態の復元
- HTTP 409発生時の最新状態の再取得
- 通信エラー発生時のエラー表示と再読み込み機能

対局開始後は設定が固定され、リセットするまで変更できません。この開始状態はSQLiteで管理されるため、ブラウザを再読み込みしても維持されます。

### CPUの思考解析

- Minimax法とαβ枝刈りによる着手選択
- 最善手・候補手ごとの評価値とペナルティの表示
- 探索深さ、探索ノード数、枝刈り回数、解析時間の表示
- 署名付き解析トークンを使った解析結果の着手への再利用
- CPU解析APIの同時実行数制限
- 古い解析結果や競合時の解析結果の破棄

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
| E2Eテスト | Playwright / Chromium |
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
│   ├── e2e/
│   │   └── game.spec.ts        # ブラウザE2Eテスト
│   ├── public/                 # 画像など
│   ├── src/
│   │   ├── api/                # FastAPIへのHTTP通信
│   │   ├── components/         # Reactコンポーネント
│   │   ├── lib/                # 共通ユーティリティ
│   │   ├── test/               # Vitest共通設定
│   │   ├── types/              # TypeScript型定義
│   │   ├── App.tsx             # オセロ画面
│   │   └── main.tsx            # React起動処理
│   ├── index.html
│   ├── package.json
│   ├── playwright.config.ts    # E2Eテスト設定
│   ├── vite.config.ts
│   └── vitest.config.ts
├── content/algorithms/         # 学習記事のMarkdown
├── static/                     # 学習ページ用CSS・JavaScript
├── templates/                  # 学習ページ用Jinja2テンプレート
├── tests/                      # Pythonテスト
├── .github/workflows/ci.yaml   # GitHub Actions
├── .env.example                # 環境変数の設定例
├── benchmark_cpu.py            # CPU探索の計測
├── compose.yaml
├── Dockerfile
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

`frontend/dist/` はViteのビルド時に生成されるディレクトリです。Gitには登録しません。

Playwrightが生成するテスト結果やスクリーンショットも、通常はGitの管理対象外です。

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

ローカル開発用の設定例：

```dotenv
SESSION_SECRET_KEY=ここに生成したランダム文字列を設定
OTHELLO_DB_PATH=data/othello.db
SESSION_COOKIE_SECURE=false
ANALYSIS_MAX_CONCURRENT=1
```

`SESSION_SECRET_KEY`には32文字以上の鍵が必要です。`.env`はGitにコミットしないでください。

各環境変数の役割は次のとおりです。

| 環境変数 | 説明 |
|---|---|
| `SESSION_SECRET_KEY` | セッションCookieとCPU解析トークンの署名に使用する秘密鍵 |
| `OTHELLO_DB_PATH` | SQLiteデータベースの保存先 |
| `SESSION_COOKIE_SECURE` | `true`の場合、セッションCookieにSecure属性を付与 |
| `ANALYSIS_MAX_CONCURRENT` | 1ワーカー内で同時に実行できるCPU解析の最大数 |

`SESSION_COOKIE_SECURE`は、ローカルHTTP環境では`false`、HTTPSで公開する本番環境では`true`を設定してください。

`ANALYSIS_MAX_CONCURRENT`の初期値は`1`です。

### 4. Reactの依存関係をインストール

Node.jsとnpmを用意し、`frontend/`で実行します。

```powershell
cd frontend
npm ci
cd ..
```

### 5. Playwrightのブラウザをインストール

E2Eテストを実行する場合に必要です。

```powershell
cd frontend
npx playwright install chromium
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

### APIのエラーと復旧

ゲーム状態の更新競合などではHTTP 409を返します。

React側では、409を受け取った際に`GET /state`で最新のゲーム状態を再取得し、盤面・対局設定・開始状態を同期します。

競合が発生した操作を自動で再送信することはありません。

CPU解析の同時実行数が上限に達した場合、`GET /analysis`はHTTP 429を返します。

レスポンスには`Retry-After`ヘッダーが設定されます。ただし、現在のReact画面は429に対する自動再試行を行いません。

## テスト・コード品質

### Backend：pytest

リポジトリのルートで実行します。

```powershell
python -m ruff check .
python -m ruff format --check .
python -m pytest -v
```

主に以下を検証します。

- オセロのルールと状態遷移
- CPUの探索アルゴリズム
- FastAPIのリクエスト・レスポンス
- SQLiteへの保存と復元
- セッション分離
- 同時更新の競合検出
- CPU解析トークンの検証
- セキュリティ設定と解析制限

### Frontend：Vitest

`frontend/`で実行します。

```powershell
cd frontend

npm run lint
npm run format:check
npm test
npm run build
```

VitestとReact Testing Libraryを使用し、主に次の動作を検証します。

- コンポーネントの表示
- 合法手の操作
- 対局開始とリセット
- CPU解析結果の表示
- API通信エラーの処理
- HTTP 409発生時の状態再同期
- 初回読み込み失敗からの復旧

整形を適用するときは次を実行します。

```powershell
npm run format
```

### E2Eテスト：Playwright

Playwrightを使用し、実際のChromiumブラウザでReact・FastAPI・SQLiteの連携をテストします。

実行前にPythonの仮想環境を有効化してください。

初回のみブラウザをインストールします。

```powershell
cd frontend
npx playwright install chromium
```

E2Eテストの実行：

```powershell
npm run test:e2e
```

テスト内容：

1. 対局を開始すると設定が固定され、再読み込み後も維持される
2. 石を置いた状態がSQLiteに保存され、再読み込み後も復元される
3. リセットすると盤面が初期化され、設定を再び変更できる
4. EasyのCPU対戦で着手と解析結果の表示が正常に動作する

現在のE2Eテストは3つのテストケースで構成されています。

#### E2Eテスト用のサーバー

`frontend/playwright.config.ts`で、Playwrightが次のサーバーを自動起動します。

| サーバー | ポート |
|---|---|
| FastAPI | 5011 |
| Vite | 5174 |

FastAPIはE2E専用のSQLiteファイル`data/othello-e2e.db`を使用します。

普段の開発で使用する`data/othello.db`とは分離されています。

ポート5011・5174をほかのプロセスが使用していないことを確認してください。

#### UIモード

Playwrightの専用画面でテストを操作できます。

```powershell
npm run test:e2e:ui
```

テストが失敗した場合、スクリーンショットやトレースを利用して原因を調査できます。

## CI：GitHub Actions

`.github/workflows/ci.yaml`で、コードの品質と動作を自動検証します。

主に以下の3ジョブを実行します。

| ジョブ | 実行内容 |
|---|---|
| `python-tests` | Ruff、pytest |
| `frontend-build` | Oxlint、Prettier、Vitest、TypeScriptチェック、Viteビルド |
| `e2e-tests` | PlaywrightによるChromium E2Eテスト |

`main`向けのPull Requestなどを契機に実行されます。

E2Eテストが失敗した場合は、GitHub Actionsの成果物としてPlaywrightのテスト結果を保存する設定になっています。

## データ保存とセッション管理

### SQLiteによる永続化

対局状態はSQLiteに保存されます。

主に以下の情報を管理します。

- 盤面
- 手番
- 対戦モード
- CPUの難易度
- 人間の石の色
- 対局開始済みかどうか
- 状態更新のバージョン番号

ブラウザを再読み込みした場合も、セッションが維持されていれば保存済みの対局を復元できます。

### セッション

Starletteの`SessionMiddleware`を使用して、ブラウザのセッションと対局を関連付けています。

セッションCookieの署名には`SESSION_SECRET_KEY`を使用します。

`SESSION_COOKIE_SECURE=true`の場合、セッションCookieにSecure属性が付きます。

本番環境ではHTTPSを使用し、この設定を有効にしてください。

### 同時更新の競合

SQLiteに保存する対局状態にはバージョン番号があります。

別のリクエストが先に状態を更新した場合、古い状態に基づく更新は競合として検出され、HTTP 409を返します。

Reactはこのエラーを受け取ると最新状態を再取得します。

ただし、複数タブの変更を常時リアルタイムに同期する機能はありません。

## セキュリティと負荷対策

### セッションCookie

- セッションCookieには署名を使用
- `SameSite=Lax`を設定
- HTTPS環境向けにSecure属性を設定可能
- 秘密鍵が未設定、または短すぎる場合はアプリの起動を拒否

### CPU解析トークン

CPU解析の結果は署名付きトークンで着手APIに渡します。

トークンには対局ID、盤面のハッシュ、状態バージョン、難易度、探索深さ、着手位置、CPUの石の色などが含まれます。

着手時にはこれらの情報を現在の対局状態と照合します。

トークンの有効期限は10分です。

### CPU解析の負荷制限

`ANALYSIS_MAX_CONCURRENT`によって、同時に実行できるCPU解析数を制限します。

上限に達した場合はHTTP 429を返します。

この制限はPythonプロセス単位です。複数ワーカーで起動した場合、全ワーカーを横断した上限にはなりません。

また、この仕組みは一定時間内のアクセス回数制限や、CPU解析の実行時間制限を保証しません。

公開規模に応じて、リバースプロキシでのレート制限やCPU計算のプロセス分離を検討してください。

## 開発上の注意事項

- ゲーム状態と開始済みフラグはSQLiteに保存されます。
- 初回表示時とHTTP 409発生時には、サーバーのゲーム状態を取得します。
- CPU解析の処理時間は難易度と局面によって変化します。
- CPU解析の同時実行制限はワーカー単位です。
- 学習ページのMinimaxデモは固定データを使用し、実際のCPU探索とは連動していません。
- E2Eテストでは専用ポートと専用SQLiteデータベースを使用します。
- 本番公開時はHTTPSと適切な秘密鍵を設定してください。
- `.env`や実際のSQLiteデータベースをGitにコミットしないでください。

## 今後の予定

### 探索アルゴリズムの可視化

- Minimaxの探索木を実際のCPU解析から生成
- αβ枝刈りによって省略されたノードの可視化
- 評価関数と候補手の比較表示
- 探索深さごとの計算量の比較

### ゲーム機能の拡張

- 対局履歴の保存
- 過去の対局の再生
- 対局結果の統計表示
- CPUアルゴリズムの比較

### 品質と運用の改善

- Firefox・WebKitを含むブラウザテスト
- 複数タブの状態同期
- CPU解析の実行時間制限
- プロセス間で共有できるレート制限
- 本番環境向けのデプロイ設定

## ライセンス

[MIT License](LICENSE)
