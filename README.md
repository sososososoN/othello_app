# Othello

PythonとJavaScriptで開発したWeb版オセロゲームです。

FastAPIをバックエンドに使用し、ゲームロジック・状態管理・API・フロントエンドを分離しています。

PvP（対人戦）とPvC（CPU対戦）に対応し、SQLiteによるゲーム状態の永続化、pytest・Vitestによる自動テスト、GitHub ActionsによるCIを導入しています。

## 主な機能

- 8×8盤面でのオセロ対局
- PvP（プレイヤー対プレイヤー）
- PvC（プレイヤー対CPU）
- Minimax法とαβ枝刈りによるCPU
- 盤面の位置評価を用いたCPUの着手選択
- 合法手の表示
- パス・ゲーム終了判定
- ゲームのリセット
- セッションごとのゲーム状態管理
- SQLiteによるゲーム状態の永続化
- 同じブラウザからの対局再開

CPUの探索順序と局面評価の改善を進めています。

## 技術スタック

| 分野 | 技術 |
|---|---|
| バックエンド | Python 3.13 / FastAPI |
| APIスキーマ | Pydantic |
| フロントエンド | HTML / CSS / JavaScript |
| テンプレート | Jinja2 |
| セッション | Starlette SessionMiddleware |
| データベース | SQLite / sqlite3 |
| Pythonテスト | pytest |
| JavaScriptテスト | Vitest / jsdom |
| Python静的解析 | Ruff |
| JavaScript静的解析 | ESLint |
| CI | GitHub Actions |
| バージョン管理 | Git / GitHub |

## ディレクトリ構成

```text
othello/
├── .github/
│   └── workflows/
│       └── ci.yaml
├── data/
│   └── othello.db             # Git管理対象外
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
│   └── test_sqlite_storage.py
├── test_js/
│   └── othello.test.js
├── .env.example
├── .gitignore
├── app.py
├── benchmark_cpu.py
├── cpu.py
├── eslint.config.mjs
├── game.py
├── LICENSE
├── package-lock.json
├── package.json
├── pytest.ini
├── pyproject.toml
├── README.md
├── requirements.txt
├── schemas.py
├── service.py
└── storage.py
```

`data/othello.db` は実行時に生成されるデータベースファイルであり、Gitでは管理しません。

`benchmark_cpu.py` はCPU探索改善の性能測定用スクリプトです。

### 各モジュールの責務

| ファイル | 役割 |
|---|---|
| `app.py` | FastAPIのエンドポイント、セッション管理、HTTPレスポンス |
| `schemas.py` | APIのリクエスト・レスポンスの型定義 |
| `service.py` | ゲーム操作やCPUターンを含むビジネスロジック |
| `storage.py` | ゲーム状態のメモリ管理・SQLite永続化 |
| `game.py` | オセロのルール、合法手、石の反転、勝敗判定 |
| `cpu.py` | CPUの着手選択、Minimax、αβ枝刈り、局面評価 |
| `static/js/othello.js` | API通信、盤面描画、ユーザー操作 |
| `benchmark_cpu.py` | CPU探索時間の測定 |
| `tests/` | Pythonのユニットテスト・APIテスト |
| `test_js/` | JavaScriptのフロントエンドテスト |

## セットアップ

### 1. リポジトリを取得

```bash
git clone <repository-url>
cd othello
```

`<repository-url>` は実際のGitHubリポジトリURLに置き換えてください。

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

Node.jsとnpmをインストールしたうえで実行します。

```powershell
npm ci
```

`npm ci` は `package-lock.json` に基づいて依存関係をインストールします。

### 5. 環境変数を設定

`.env.example` を参考に `.env` を作成します。

```dotenv
SESSION_SECRET_KEY=replace-with-a-long-random-secret
OTHELLO_DB_PATH=data/othello.db
```

セッション署名鍵は、次のコマンドで生成できます。

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

生成した文字列を `SESSION_SECRET_KEY` に設定してください。

`.env` には秘密情報が含まれるため、Gitにコミットしないでください。

## アプリケーションの起動

`.env` を利用する場合：

```powershell
python -m uvicorn app:app --reload --port 5001 --env-file .env
```

この方法では、Uvicornの環境変数ファイル読み込み機能を使用します。必要に応じて `python-dotenv` をインストールしてください。

```powershell
python -m pip install python-dotenv
```

環境変数をPowerShellで直接指定する場合：

```powershell
$env:SESSION_SECRET_KEY = "YOUR_SECRET_KEY"
$env:OTHELLO_DB_PATH = "data/othello.db"

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

`y` は行、`x` は列を表します。座標は0から7までです。

### モード切り替えのリクエスト例

`PATCH /mode`

```json
{
  "mode": "pvc"
}
```

`mode` は以下の値を指定します。

- `pvp`：プレイヤー対プレイヤー
- `pvc`：プレイヤー対CPU

### レスポンス例

```json
{
  "board": [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 2, 1, 0, 0, 0],
    [0, 0, 0, 1, 2, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0]
  ],
  "turn": 1,
  "message": "",
  "mode": "pvp",
  "valid_moves": [
    [2, 3],
    [3, 2],
    [4, 5],
    [5, 4]
  ]
}
```

盤面の値は以下の意味を持ちます。

| 値 | 意味 |
|---|---|
| `0` | 空きマス |
| `1` | 黒 |
| `2` | 白 |

ゲーム状態はJSON形式で返却されます。

Pydanticを使用して座標やゲームモードを検証し、不正な着手やゲーム状態に応じた操作エラーをAPI側で処理します。

## CPUの探索アルゴリズム

PvCモードではCPUが白を担当します。

CPUの着手選択には、Minimax法とαβ枝刈りを使用しています。

### Minimax法

Minimax法は、双方が最適な着手を選択すると仮定して、ゲーム木を探索するアルゴリズムです。

- CPU（白）：評価値を最大化
- プレイヤー（黒）：評価値を最小化

### αβ枝刈り

αβ枝刈りは、最終的な選択に影響しない探索枝を省略する手法です。

探索結果の最適性を維持しながら、探索する局面数を削減できます。

### 着手順序の最適化

CPU探索改善では、位置評価テーブルを使用して合法手を並べ替え、有望な着手から探索する方式を導入しています。

これにより、αβ枝刈りの効果を高めることを狙っています。

ただし、探索効率の改善量は盤面や着手順序によって異なります。

### 局面評価

CPU探索改善では、以下の要素を評価関数に組み込んでいます。

- 盤面上の石の位置評価
- 白と黒の合法手数の差（Mobility）
- 角の確保状況
- 終盤の石数差
- 終局時の勝敗評価

序盤・中盤の評価式：

\[
E(s)=P(s)+5M(s)+25C(s)
\]

- \(P(s)\)：位置評価テーブルによる白と黒の評価値の差
- \(M(s)\)：白の合法手数 − 黒の合法手数
- \(C(s)\)：白の角の確保数 − 黒の角の確保数

白に有利な局面ほど高い評価値を返します。

係数は暫定値であり、CPUの強さが改善したことを保証するものではありません。

### 探索深さ

デフォルトの探索深さは、盤面の石数によって変化します。

| 条件 | 探索深さ |
|---|---|
| 石数が48個以下 | 4 |
| 石数が48個を超える | 5 |

`choose_cpu_move()` の `depth` は、CPUが着手した後にMinimaxで探索する深さを表します。

### CPU性能測定

CPUの探索時間を測定するため、`benchmark_cpu.py` を用意しています。

```powershell
python benchmark_cpu.py
```

初期盤面での測定例：

| depth | CPUの着手 | 平均実行時間 |
|---|---|---:|
| 1 | (2, 4) | 0.0031秒 |
| 2 | (2, 4) | 0.0135秒 |
| 3 | (2, 4) | 0.0399秒 |
| 4 | (2, 4) | 0.1170秒 |

この測定結果は特定の開発環境・初期盤面におけるものです。

実行時間はCPU性能、探索深さ、盤面の進行状況、合法手数によって変化します。

中盤・終盤での性能や、旧CPUと比較した勝率の改善は今後検証する予定です。

## ゲーム状態の永続化

SQLiteを使用してゲーム状態を保存しています。

保存対象は以下のとおりです。

- ゲームID
- 8×8盤面
- 現在の手番
- ゲームモード
- ゲームメッセージ

ゲーム状態は `data/othello.db` に保存されます。

ゲームの状態変更後にデータベースへ保存するため、サーバープロセスを再起動しても対局を復元できます。

### セッション管理

ゲームはセッションCookieに紐づくゲームIDで識別します。

再起動後の復元には、以下の条件が必要です。

- 同じSQLiteデータベースを使用すること
- `SESSION_SECRET_KEY` が変わっていないこと
- ブラウザに有効なセッションCookieが残っていること

ブラウザごとにCookieの保存領域が異なるため、異なるブラウザや端末では原則として同じ対局を共有できません。

### ストレージ構成

`storage.py` には、以下のストレージを実装しています。

| クラス | 役割 |
|---|---|
| `GameStore` | メモリ上でゲーム状態を管理 |
| `SQLiteGameStore` | SQLiteによるゲーム状態の保存・復元 |

`SQLiteGameStore` はメモリキャッシュとSQLiteを組み合わせた構成です。

`GameService` はゲーム状態を変更した後、ストレージへ保存します。

保存処理やゲーム操作の途中で例外が発生した場合は、メモリ上の変更を元に戻す処理を備えています。

現段階では単一サーバープロセスでの使用を想定しています。

## テスト

### Python

pytestを使用して、以下を検証します。

- ゲームロジック
- CPUの着手選択
- APIの正常系・異常系
- Pydanticスキーマ
- ゲームサービス
- セッション分離
- メモリストレージ
- SQLiteの保存・復元
- SQLite更新失敗時の処理

すべてのPythonテストを実行：

```powershell
python -m pytest -v
```

SQLite関連テスト：

```powershell
python -m pytest tests/test_sqlite_storage.py -v
```

CPU関連テスト：

```powershell
python -m pytest tests/test_cpu.py -v
```

### JavaScript

フロントエンドのテストは `test_js/` に配置しています。

Vitestとjsdomを使用し、API通信をモックしてブラウザ側の振る舞いを検証します。

主なテスト対象：

- 初期盤面の描画
- 石と合法手の表示
- 合法手クリック時のAPIリクエスト
- 不正なマスのクリック防止
- リセット操作
- PvP/PvC切り替え
- 通信エラー時の表示と復旧
- ゲーム終了時・CPU手番時の表示
- 通信中の二重リクエスト防止

テスト実行：

```powershell
npm test
```

開発中の自動再実行：

```powershell
npm run test:watch
```

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

自動修正後はGit差分を確認し、テストを再実行してください。

### JavaScript：ESLint

```powershell
npm run lint
```

未定義変数や未使用変数などの問題を検出します。

### コミット前の確認

```powershell
python -m ruff check .
python -m ruff format --check .
python -m pytest -v
npm run lint
npm test
```

## CI：GitHub Actions

`.github/workflows/ci.yaml` でCIを管理しています。

### Pythonジョブ

1. Python環境のセットアップ
2. 依存関係のインストール
3. RuffによるLint
4. Ruffによるフォーマットチェック
5. pytest

### JavaScriptジョブ

1. Node.js環境のセットアップ
2. 依存関係のインストール
3. ESLint
4. Vitest

### CIの発火条件

- `main` および設定された開発ブランチへのpush：対象ファイルの変更があった場合
- `main` 向けPull Request：ファイルの種類にかかわらず実行
- 手動実行：GitHub ActionsまたはGitHub CLI

ワークフローは読み取り専用権限を基本とし、コードの自動commit・pushやデプロイは行いません。

### GitHub CLIで実行状況を確認

```powershell
gh run list --workflow ci.yaml --limit 5
```

失敗した実行のログを確認：

```powershell
gh run view <RUN_ID> --log-failed
```

`<RUN_ID>` は実際の実行IDに置き換えてください。

## 開発フロー

このプロジェクトではGitHub Flowを基本として開発しています。

1. `main` ブランチを最新の状態に更新する
2. `main` から作業ブランチを作成する
3. 機能追加・修正・テストを実施する
4. 必要に応じてREADMEを更新する
5. ローカルでLint・Format・テストを実行する
6. 変更内容ごとにコミットする
7. GitHubへpushする
8. `main` に向けてPull Requestを作成する
9. GitHub ActionsのCI成功を確認する
10. Pull Requestをマージする

### ブランチ保護

`main` にはGitHub Rulesetを適用しています。

以下の操作を制限します。

- 直接push
- 強制push
- ブランチ削除

また、マージには以下のCIチェックの成功が必要です。

- `Python / pytest`：Ruff・pytest
- `JavaScript / Vitest`：ESLint・Vitest

## 現在の制約

- SQLiteによる永続化は単一サーバープロセス向けです。
- 複数ワーカーによる同一ゲームの並行更新には対応していません。
- 異なるブラウザや端末間での対局共有には対応していません。
- 対局復元には有効なセッションCookieと固定の署名鍵が必要です。
- CPU難易度のユーザー選択機能は未実装です。
- CPU探索の性能は盤面によって変化し、応答時間の上限は保証されません。
- 本番環境へのデプロイ・監視は未整備です。

現時点では開発・学習用途を中心とした構成です。

## 開発状況と今後の予定

### 完了済み

- [x] オセロの基本ルール・勝敗判定
- [x] PvP・PvCモード
- [x] ゲームロジックとAPIの分離
- [x] FastAPIへの移行
- [x] PydanticによるAPIスキーマ検証
- [x] pytestによるバックエンドテスト
- [x] Vitestによるフロントエンドテスト
- [x] Ruff・ESLintによる静的解析
- [x] GitHub ActionsによるCI
- [x] mainブランチの保護とPRベースの開発フロー
- [x] SQLiteによるゲーム状態の永続化

### 開発中・今後の予定

- [ ] CPUの探索順序・局面評価の改善をマージ
- [ ] Easy / Normal / HardのCPU難易度選択
- [ ] 中盤・終盤のCPU探索性能測定
- [ ] CPU評価関数の調整・旧CPUとの対戦比較
- [ ] Dockerによる開発・実行環境の統一
- [ ] 本番環境へのデプロイ
- [ ] ログ・監視の整備
- [ ] 対局履歴・ブラウザ間の対局復元機能の検討

## ライセンス

このプロジェクトは [MIT License](LICENSE) のもとで公開されています。