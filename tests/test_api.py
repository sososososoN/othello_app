from fastapi.testclient import TestClient

import service as game_service
from schemas import GameStateResponse


def test_index(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "オセロ" in response.text


def test_static_files(client: TestClient) -> None:
    assert client.get("/static/css/style.css").status_code == 200
    assert client.get("/static/js/othello.js").status_code == 200


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
