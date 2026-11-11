from fastapi.testclient import TestClient

import backend.service as game_service
from backend.schemas import GameStateResponse
import backend.app as othello
from backend.storage import SQLiteGameStore, GameRecord
from backend.game import BLACK, WHITE


def test_index(client: TestClient, monkeypatch, tmp_path) -> None:
    index_file = tmp_path / "index.html"
    index_file.write_text(
        "<!doctpe html><html><head><title>Othello AI Lab</title></head>"
        '<body><div id="root"></div></body></html>',
        encoding="utf-8",
    )
    monkeypatch.setattr(othello, "FRONTEND_DIST_DIR", tmp_path)
    response = client.get("/")
    assert response.status_code == 200
    assert "Othello AI Lab" in response.text
    assert '<div id="root"></div>' in response.text
    assert response.headers["content-type"].startswith("text/html")


def test_static_files(client: TestClient) -> None:
    assert client.get("/static/css/learning.css").status_code == 200
    assert client.get("/static/js/minimax_demo.js").status_code == 200
    assert client.get("/static/css/style.css").status_code == 404
    assert client.get("/static/js/othello.js").status_code == 404


def test_initial_state(client: TestClient) -> None:
    response = client.get("/state")

    assert response.status_code == 200

    data = response.json()
    assert data["turn"] == 1
    assert len(data["valid_moves"]) == 4


def test_valid_move(client: TestClient) -> None:
    response = client.post(
        "/moves",
        json={"y": 2, "x": 3},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["board"][2][3] == 1
    assert data["board"][3][3] == 1
    assert data["turn"] == 2


def test_reset(client: TestClient) -> None:
    move_response = client.post(
        "/moves",
        json={"y": 2, "x": 3},
    )
    assert move_response.status_code == 200

    response = client.post("/reset", json={})

    assert response.status_code == 200

    data = response.json()
    assert data["turn"] == 1
    assert sum(row.count(1) for row in data["board"]) == 2
    assert sum(row.count(2) for row in data["board"]) == 2


def test_invalid_coordinates(client: TestClient) -> None:
    response = client.post(
        "/moves",
        json={"y": 100, "x": 3},
    )

    # Pydanticの座標範囲検証で422になる
    assert response.status_code == 422


def test_invalid_coordinate_type(client: TestClient) -> None:
    response = client.post(
        "/moves",
        json={"y": "hello", "x": 3},
    )

    assert response.status_code == 422


def test_invalid_json(client: TestClient) -> None:
    response = client.post(
        "/moves",
        json=[1, 2, 3],
    )

    assert response.status_code == 422


def test_invalid_mode(client: TestClient) -> None:
    response = client.patch(
        "/mode",
        json={"mode": "other"},
    )

    assert response.status_code == 422


def test_illegal_move(client: TestClient) -> None:
    response = client.post(
        "/moves",
        json={"y": 0, "x": 0},
    )

    assert response.status_code == 400
    assert response.json()["error"] == "Illegal move"


def test_cpu_game(client: TestClient, monkeypatch) -> None:
    # CPUの探索処理を固定の着手で置き換える
    monkeypatch.setattr(
        game_service,
        "choose_cpu_move",
        lambda board, depth: (2, 2),
    )

    mode_response = client.patch(
        "/mode",
        json={"mode": "pvc"},
    )
    assert mode_response.status_code == 200

    response = client.post(
        "/moves",
        json={"y": 2, "x": 3},
    )

    assert response.status_code == 200

    state = response.json()
    assert state["board"][2][2] == 2
    assert state["turn"] == 1
    assert state["mode"] == "pvc"


def test_mode_change_after_move(client: TestClient) -> None:
    move_response = client.post(
        "/moves",
        json={"y": 2, "x": 3},
    )
    assert move_response.status_code == 200

    response = client.patch(
        "/mode",
        json={"mode": "pvc"},
    )

    assert response.status_code == 409


def test_state(client: TestClient) -> None:
    response = client.get("/state")

    assert response.status_code == 200
    assert response.json()["turn"] == 1


def test_openapi(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/state" in paths
    assert "/moves" in paths
    assert "/mode" in paths
    assert "/reset" in paths

    # 旧APIが削除されていることを確認
    assert "/click" not in paths


def test_response_schema(client: TestClient) -> None:
    response = client.get("/state")

    assert response.status_code == 200

    state = GameStateResponse.model_validate(response.json())

    assert len(state.board) == 8
    assert all(len(row) == 8 for row in state.board)
    assert state.turn == 1


def test_openapi_response_schema(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    for method, path in (
        ("get", "/state"),
        ("post", "/moves"),
        ("patch", "/mode"),
        ("post", "/reset"),
    ):
        schema = paths[path][method]["responses"]["200"]["content"]["application/json"][
            "schema"
        ]

        assert schema["$ref"].endswith("/GameStateResponse")


def test_change_mode(client: TestClient) -> None:
    response = client.patch(
        "/mode",
        json={"mode": "pvc"},
    )

    assert response.status_code == 200
    assert response.json()["mode"] == "pvc"


def test_old_click_endpoint_removed(client: TestClient) -> None:
    response = client.post(
        "/click",
        json={"y": 2, "x": 3, "mode": "pvp"},
    )

    assert response.status_code == 404


def test_change_difficulty_api(client) -> None:

    client.get("/state")

    mode_response = client.patch(
        "/mode",
        json={"mode": "pvc"},
    )
    assert mode_response.status_code == 200

    response = client.patch(
        "/difficulty",
        json={"difficulty": "hard"},
    )

    assert response.status_code == 200
    assert response.json()["difficulty"] == "hard"

    restored = client.get("/state")
    assert restored.json()["difficulty"] == "hard"


def test_invalid_difficulty_returns_422(client) -> None:
    response = client.patch(
        "/difficulty",
        json={"difficulty": "expert"},
    )

    assert response.status_code == 422


def test_difficulty_requires_pvc_api(client) -> None:
    response = client.patch(
        "/difficulty",
        json={"difficulty": "easy"},
    )

    assert response.status_code == 409


def test_analysis_requires_pvc(client: TestClient) -> None:
    """PvPモードでは解析を拒否する。"""
    response = client.get("/analysis?depth=1")
    assert response.status_code == 409


def test_analysis_requires_cpu_turn(client: TestClient) -> None:
    """PvCでも黒の手番では解析を拒否する。"""
    response = client.patch(
        "/mode",
        json={"mode": "pvc"},
    )
    assert response.status_code == 200

    response = client.get("/analysis?depth=1")
    assert response.status_code == 409


def test_analysis_returns_candidates(client: TestClient) -> None:
    """白の手番で全候補手の評価結果を取得する。"""
    assert (
        client.patch(
            "/mode",
            json={"mode": "pvc"},
        ).status_code
        == 200
    )

    # /movesではCPUも動くので/playerを使用する
    response = client.post(
        "/moves/player",
        json={"y": 2, "x": 3},
    )
    assert response.status_code == 200
    assert response.json()["turn"] == 2

    response = client.get("/analysis?depth=1")
    assert response.status_code == 200

    data = response.json()
    assert data["depth"] == 1
    assert data["best_move"] is not None
    assert data["nodes_visited"] > 0
    assert len(data["candidates"]) == 3

    # 候補手の集合が白の合法手と一致する
    assert {tuple(item["move"]) for item in data["candidates"]} == {
        (2, 2),
        (2, 4),
        (4, 2),
    }

    # 最善手が最大スコアの候補になっている
    best = max(
        data["candidates"],
        key=lambda item: item["total_score"],
    )
    assert data["best_move"] == best["move"]
    assert data["score"] == best["total_score"]

    # 既存のCPU評価式を確認する
    for item in data["candidates"]:
        assert item["total_score"] == (item["minimax_score"] - item["penalty"] * 2)


def test_analysis_depth_validation(client: TestClient) -> None:
    """範囲外や整数でないdepthを422で拒否する。"""
    for depth in ("-1", "6", "abc", "1.5"):
        response = client.get(
            "/analysis",
            params={"depth": depth},
        )
        assert response.status_code == 422


def test_analysis_uses_difficulty(client: TestClient) -> None:
    """depth省略時は対局の難易度を使用する。"""
    assert (
        client.patch(
            "/mode",
            json={"mode": "pvc"},
        ).status_code
        == 200
    )

    assert (
        client.patch(
            "/difficulty",
            json={"difficulty": "easy"},
        ).status_code
        == 200
    )

    assert (
        client.post(
            "/moves/player",
            json={"y": 2, "x": 3},
        ).status_code
        == 200
    )

    response = client.get("/analysis")
    assert response.status_code == 200
    assert response.json()["depth"] == 1


def test_analysis_preserves_state(client: TestClient) -> None:
    """解析しても盤面・手番・対局設定は変更されない。"""
    assert (
        client.patch(
            "/mode",
            json={"mode": "pvc"},
        ).status_code
        == 200
    )

    assert (
        client.post(
            "/moves/player",
            json={"y": 2, "x": 3},
        ).status_code
        == 200
    )

    before = client.get("/state").json()

    assert client.get("/analysis?depth=1").status_code == 200

    after = client.get("/state").json()
    assert after == before


def test_analysis_openapi_schema(client: TestClient) -> None:
    """OpenAPIに解析APIの応答モデルが登録される。"""
    response = client.get("/openapi.json")
    assert response.status_code == 200

    path = response.json()["paths"]["/analysis"]["get"]
    schema = path["responses"]["200"]["content"]["application/json"]["schema"]

    assert schema["$ref"].endswith("/AnalysisResponse")


def test_api_reads_latest_state_from_other_store(
    client: TestClient,
    monkeypatch,
    tmp_path,
) -> None:
    """他ストアの更新を次のAPIリクエストで取得できる。"""
    db_path = tmp_path / "concurrency.db"
    store_a = SQLiteGameStore(db_path)
    monkeypatch.setattr(othello, "store", store_a)

    # API側に対局を作成する
    assert client.get("/state").status_code == 200
    game_id = next(iter(store_a._records))

    # 別ワーカーに相当するストアで着手する
    store_b = SQLiteGameStore(db_path)
    record_b = store_b.get(game_id)
    assert record_b is not None

    game_service.GameService(record_b).play(2, 3)

    # API側は更新後の盤面を取得できる
    response = client.get("/state")

    assert response.status_code == 200
    assert response.json()["board"][2][3] == BLACK
    assert response.json()["turn"] == WHITE

    # 最新の盤面では(3,2)は合法手でない
    invalid = client.post("/moves", json={"y": 3, "x": 2})
    assert invalid.status_code == 400
    assert invalid.json()["error"] == "Illegal move"


def test_concurrent_update_returns_409(
    client: TestClient,
    monkeypatch,
    tmp_path,
) -> None:
    """読み取り後に更新競合が発生した場合は409を返す。"""
    db_path = tmp_path / "concurrency.db"
    store_a = SQLiteGameStore(db_path)
    monkeypatch.setattr(othello, "store", store_a)

    # APIで初期対局を作る
    assert client.get("/state").status_code == 200

    # API側の保存メソッドを退避
    original_save = store_a._save
    store_b = SQLiteGameStore(db_path)

    def save_with_concurrent_update(
        target_id: str,
        record: GameRecord,
    ) -> None:
        # APIが盤面を読んだ後、保存する直前に
        # 別ワーカーが同じ対局を更新した状況を再現する
        other = store_b.get(target_id)
        assert other is not None

        game_service.GameService(other).play(2, 3)

        # API側が古いversionで保存しようとする
        original_save(target_id, record)

    monkeypatch.setattr(
        store_a,
        "_save",
        save_with_concurrent_update,
    )

    response = client.post(
        "/moves",
        json={"y": 3, "x": 2},
    )

    assert response.status_code == 409
    assert response.json()["error"] == ("Game state was updated by another request")

    # 競合後、最新の盤面を取得できる
    refreshed = client.get("/state")
    assert refreshed.status_code == 200
    assert refreshed.json()["board"][2][3] == BLACK
    assert refreshed.json()["turn"] == WHITE


def test_analyzed_cpu_move_reuses_best_move(
    client: TestClient,
    monkeypatch,
) -> None:
    """解析済みの最善手を使い、CPU探索を再実行しない。"""

    # 計算時間を短くするためEasyを使用
    assert client.patch("/mode", json={"mode": "pvc"}).status_code == 200

    assert client.patch("/difficulty", json={"difficulty": "easy"}).status_code == 200

    assert client.post("/moves/player", json={"y": 2, "x": 3}).status_code == 200

    # 先に解析して署名付きトークンを取得
    response = client.get("/analysis")
    assert response.status_code == 200

    analysis = response.json()
    token = analysis["analysis_token"]

    assert isinstance(token, str)
    assert token

    # ここから再探索が行われたら失敗させる
    def fail_search(*args, **kwargs):
        raise AssertionError("CPU search was executed again")

    monkeypatch.setattr(
        game_service,
        "choose_cpu_move",
        fail_search,
    )

    # 解析結果を再利用してCPUが着手する
    move_response = client.post(
        "/moves/cpu",
        json={"analysis_token": token},
    )

    assert move_response.status_code == 200, move_response.json()

    # 実際に置かれた白石が解析の最善手と一致
    y, x = analysis["best_move"]
    state = move_response.json()

    assert state["board"][y][x] == WHITE
    assert state["turn"] == BLACK


def test_cpu_rejects_invalid_analysis_token(client: TestClient) -> None:
    response = client.post(
        "/moves/cpu",
        json={"analysis_token": "invalid-token"},
    )
    assert response.status_code == 400
