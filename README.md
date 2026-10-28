# Othello Web App

PythonのFlaskで構築したWeb版オセロアプリケーションです。

プレイヤー同士の対戦（PvP）とCPU対戦（PvC）に対応しています。CPUにはMinimax法とαβ枝刈りを使用しています。

## 主な機能

- 8×8のオセロ盤面
- プレイヤー対プレイヤー（PvP）
- プレイヤー対CPU（PvC）
- 合法手のハイライト表示
- 石の反転、パス、終局判定
- ゲームのリセット
- ブラウザのセッションごとのゲーム状態管理
- ページ再読み込み後の対局状態の復元
- pytestによる自動テスト

## 技術スタック

| 分野 | 技術 |
|---|---|
| Backend | Python 3.13 / Flask |
| Frontend | HTML / CSS / JavaScript |
| CPU | Minimax / Alpha-Beta Pruning |
| Storage | Pythonのインメモリ辞書 |
| Session | Flask Session |
| Testing | pytest |
| Version Control | Git / GitHub |

## ディレクトリ構成

```text
オセロ_app/
├── app.py
├── game.py
├── cpu.py
├── storage.py
├── service.py
├── requirements.txt
├── pytest.ini
├── README.md
├── .gitignore
├── templates/
│   └── index.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── othello.js
└── tests/
    ├── conftest.py
    ├── test_game.py
    ├── test_game_model.py
    ├── test_cpu.py
    ├── test_api.py
    ├── test_session.py
    ├── test_storage.py
    └── test_service.py
```

## アーキテクチャ

責務を分離したレイヤード構成を採用しています。

| ファイル | 責務 |
|---|---|
| `app.py` | HTTPリクエスト、セッション、レスポンス |
| `service.py` | 対戦モード変更、ゲーム進行、CPUの応手 |
| `game.py` | 盤面、合法手、石の反転、パス、終局 |
| `cpu.py` | 盤面評価、Minimax探索、CPUの着手選択 |
| `storage.py` | ゲームIDとゲーム状態の保存・取得・削除 |

ゲームの進行処理をFlaskから分離しているため、ドメインロジックやサービス層はHTTPサーバーを起動せずにテストできます。

### データフロー

```text
Browser
   |
   | HTTP Request
   v
app.py
   |
   | GameService
   v
service.py
   |
   +---- game.py
   |
   +---- cpu.py
   |
   +---- storage.py（GameRecord）
   |
   v
app.py
   |
   | JSON Response
   v
Browser
```

## セットアップ

### 1. リポジトリの取得

```powershell
git clone <repository-url>
cd オセロ_app
```

### 2. 仮想環境の作成

```powershell
py -3.13 -m venv .venv
```

### 3. 仮想環境の有効化

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

終了する場合:

```powershell
deactivate
```

### 4. 依存パッケージのインストール

```powershell
python -m pip install -r requirements.txt
```

### 5. アプリケーションの起動

```powershell
python app.py
```

ブラウザから次のURLにアクセスします。

http://127.0.0.1:5001/

Flaskの開発サーバーを使用しているため、本番環境での公開には別途適切なWSGIサーバーなどが必要です。

## API仕様

### `GET /`

ゲーム画面のHTMLを返します。セッションにゲームが存在しない場合は新規作成します。

### `GET /state`

現在のゲーム状態を取得します。

### `POST /click`

指定座標に石を置きます。

リクエスト例：

```json
{
  "y": 2,
  "x": 3,
  "mode": "pvp"
}
```

座標は0始まりです。

`y = -1`、`x = -1` は既存フロントエンドとの互換性のために残している状態取得用の特別な指定です。

### `POST /reset`

現在のセッションのゲーム盤面を初期化します。対戦モードは維持します。

### レスポンス形式

```json
{
  "board": [
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

上記の `board` は形式を説明するために1行のみ示しています。実際には8行8列の整数配列が返ります。

盤面の値：

- `0`：空きマス
- `1`：黒石
- `2`：白石

`turn` はゲーム終了時に `0` となります。

入力エラーにはHTTP 400、ゲーム状態との競合にはHTTP 409を使用します。

## CPUのアルゴリズム

CPUは白石を担当します。

Minimax法を使用し、プレイヤーが最善手を選択することを前提に先読み探索を行います。

さらにαβ枝刈りによって、最終的な判断に影響しない探索分岐を省略します。

盤面評価では以下を考慮しています。

- 角などの位置の価値
- 石数の差
- 終局時の勝敗
- 反転する石の周囲の空きマス

探索深さは基本4、盤上の石が48個を超えた場合は5に設定しています（明示的な深さ指定がない場合）。

## テスト

pytestを使用します。

### 全テストを実行

```powershell
python -m pytest -v
```

### 個別テストを実行

```powershell
python -m pytest tests/test_game_model.py -v
python -m pytest tests/test_cpu.py -v
python -m pytest tests/test_api.py -v
python -m pytest tests/test_session.py -v
python -m pytest tests/test_storage.py -v
python -m pytest tests/test_service.py -v
```

各テストの主な対象は次のとおりです。

| テスト | 検証対象 |
|---|---|
| `test_game_model.py` | オセロのルールと状態遷移 |
| `test_cpu.py` | CPU探索と盤面評価 |
| `test_api.py` | HTTP APIの入出力 |
| `test_session.py` | セッションの独立性 |
| `test_storage.py` | ゲームの保存・取得・削除 |
| `test_service.py` | ゲーム進行とCPU連携 |

## セッションとゲーム状態の管理

ブラウザのセッションCookieにはゲームIDを保存します。

サーバー側では `GameStore` がゲームIDと `GameRecord` の対応関係を保持します。

`GameRecord` には以下の情報があります。

- `Game` インスタンス
- 対戦モード
- 排他制御用のロック

同じブラウザセッションでは対局を継続でき、別のブラウザセッションでは独立したゲームを利用できます。

## 現在の制約

このプロジェクトは学習・ローカル開発向けの構成です。

- ゲーム状態はメモリ内に保存され、サーバー再起動で消失します。
- 複数のPythonプロセス間ではゲーム状態を共有できません。
- ログイン認証は実装していません。
- 古いゲームを自動削除する仕組みは未実装です。
- CSRF対策や本番向けセッション設定は追加検討が必要です。
- CPU探索は同期的に実行するため、探索が長い場合はレスポンスが遅くなります。

## 今後の改善候補

- ゲーム状態の永続化（Redis / PostgreSQL）
- ゲームデータの有効期限と自動削除
- CPU探索の高速化
- 難易度の選択
- WebSocketを利用したリアルタイム対戦
- CIによる自動テスト
- デプロイ環境の整備

## 開発方針

機能追加だけでなく、リファクタリングを通じて次の設計原則を学ぶことを目的としています。

- Separation of Concerns（関心の分離）
- Encapsulation（カプセル化）
- Dependency Injection（依存性注入）
- Service Layer（サービス層）
- Repository Pattern（リポジトリパターン）
- Automated Testing（自動テスト）

変更後はpytestとブラウザで動作確認を行い、正常動作を確認してからGitにコミットします。