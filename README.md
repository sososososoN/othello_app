# Othello

PythonとJavaScriptで開発したWeb版オセロゲームです。

FastAPIをバックエンドに使用し、ゲームロジック・状態管理・API・フロントエンドを分離しています。

## 主な機能

- 8×8盤面でのオセロ対局
- PvP（プレイヤー対プレイヤー）
- PvC（プレイヤー対CPU）
- Minimax法とαβ枝刈りによるCPU
- 合法手の表示
- パス・ゲーム終了判定
- ゲームのリセット
- セッションごとのゲーム状態管理

## 技術スタック

| 分野 | 技術 |
|---|---|
| バックエンド | Python 3.13 / FastAPI |
| APIスキーマ | Pydantic |
| フロントエンド | HTML / CSS / JavaScript |
| テンプレート | Jinja2 |
| セッション | Starlette SessionMiddleware |
| Pythonテスト | pytest |
| JavaScriptテスト | Vitest / jsdom |
| Python静的解析 | Ruff |
| JavaScript静的解析 | ESLint |
| CI | GitHub Actions |

## ディレクトリ構成

```text
othello/
├── .github/
│   └── workflows/
│       └── ci.yaml
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── othello.js
├── templates/
│   └── index.html
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_cpu.py
│   ├── test_game.py
│   ├── test_game_model.py
│   ├── test_schemas.py
│   ├── test_service.py
│   ├── test_session.py
│   ├── test_storage.py
│   └── othello.test.js
├── app.py
├── cpu.py
├── game.py
├── schemas.py
├── service.py
├── storage.py
├── requirements.txt
├── package.json
├── package-lock.json
├── pytest.ini
├── pyproject.toml
├── eslint.config.mjs
└── README.md
```

### 各モジュールの責務

| ファイル | 役割 |
|---|---|
| `app.py` | FastAPIのエンドポイント、セッション、HTTPレスポンス |
| `schemas.py` | APIのリクエスト・レスポンスの型定義 |
| `service.py` | ゲーム操作やCPUターンを含むビジネスロジック |
| `storage.py` | セッションに対応するゲーム状態の管理 |
| `game.py` | オセロのルール、合法手、石の反転、勝敗判定 |
| `cpu.py` | CPUの着手選択、Minimax、αβ枝刈り |
| `othello.js` | API通信、盤面描画、ユーザー操作 |

## セットアップ

### 1. リポジトリを取得

```bash
git clone <repository-url>
cd othello
```

### 2. Pythonの仮想環境を作成

Windows PowerShellの場合：

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Pythonの依存関係をインストール

```powershell
python -m pip install -r requirements.txt
```

### 4. JavaScriptの依存関係をインストール

Node.jsとnpmをインストールしたうえで、以下を実行します。

```powershell
npm ci
```

## アプリケーションの起動

```powershell
python -m uvicorn app:app --reload --port 5001
```

ブラウザから以下にアクセスします。

- アプリ：http://127.0.0.1:5001/
- APIドキュメント：http://127.0.0.1:5001/docs

`--reload` は開発用オプションです。

## API

| Method | Endpoint | 説明 |
|---|---|---|
| GET | `/` | ゲーム画面を表示 |
| GET | `/state` | 現在のゲーム状態を取得 |
| POST | `/moves` | 指定座標に石を置く |
| PATCH | `/mode` | PvPとPvCを切り替える |
| POST | `/reset` | ゲームを初期化 |

### 着手のリクエスト例

`POST /moves`

```json
{
  "y": 2,
  "x": 3
}
```

### モード切り替えのリクエスト例

`PATCH /mode`

```json
{
  "mode": "pvc"
}
```

ゲーム状態はJSON形式で返却されます。

座標やモードの入力はPydanticで検証します。不正な着手やゲーム状態に応じた操作エラーは、API側で処理します。

## テスト

### Python

```powershell
python -m pytest -v
```

ゲームロジック、CPU、API、スキーマ、セッション、ストレージなどを検証します。

### JavaScript

```powershell
npm test
```

Vitestとjsdomを使用して、ブラウザ側の処理を検証します。

## 静的解析・フォーマット

### Python：Ruff

Lint：

```powershell
python -m ruff check .
```

フォーマットチェック：

```powershell
python -m ruff format --check .
```

自動修正：

```powershell
python -m ruff check --fix .
python -m ruff format .
```

自動修正後は差分を確認し、テストを再実行してください。

### JavaScript：ESLint

```powershell
npm run lint
```

未定義変数や未使用変数などを検出します。

## CI：GitHub Actions

`.github/workflows/ci.yaml` でCIを管理します。

CIでは次のチェックを実行します。

**Python**
1. 依存関係のインストール
2. RuffによるLint
3. Ruffによるフォーマットチェック
4. pytest

**JavaScript**
1. 依存関係のインストール
2. ESLint
3. Vitest

ワークフローは、設定されたブランチとファイル変更条件に基づいて起動します。

ワークフローの権限は原則として読み取り専用とし、テストのためにコードを自動commit・pushする処理は設けていません。

### GitHub CLIで実行状況を確認

```powershell
gh run list --workflow ci.yaml --limit 5
```

失敗した実行のログは、実行IDを指定して確認します。

```powershell
gh run view <RUN_ID> --log-failed
```

## 開発フロー

開発は原則として作業ブランチで行い、変更単位を分けてcommitします。

1. 作業ブランチで機能追加・修正を行う
2. ローカルでLint・Format・テストを実行する
3. 必要に応じてREADMEを更新する
4. 変更内容ごとにcommitする
5. GitHubにpushする
6. CIの結果を確認する
7. Pull Requestを通じてmainへの統合を行う

CIを必須チェックとするブランチ保護は、設定の整合性を確認したうえで導入します。

## 現在の制約

ゲーム状態はサーバーのメモリ上に保持しています。

そのため、サーバープロセスを再起動すると対局状態は失われます。また、複数プロセス間でゲーム状態を共有する仕組みもありません。

現時点では、開発・学習用途を中心とした構成です。

## 今後の予定

- [ ] CIの最終確認とmainブランチ保護
- [ ] JavaScriptのテストケース拡充
- [ ] SQLiteによるゲーム状態の永続化
- [ ] CPUの探索性能改善・難易度設定
- [ ] Dockerによる開発・実行環境の統一
- [ ] 本番環境へのデプロイと監視

## ライセンス

このプロジェクトは [MIT License](LICENSE) のもとで公開されています。