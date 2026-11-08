import pytest
from fastapi.testclient import TestClient

import app as othello
import service as service_module
from game import BLACK, WHITE


def start_pvc(
    client: TestClient,
    human_order: str = "first",
) -> dict:
    """EasyのCPU対戦を開始し、状態を返す。"""
    response = client.post(
        "/games/start",
        json={
            "mode": "pvc",
            "difficulty": "easy",
            "human_order": human_order,
        },
    )
    assert response.status_code == 200, response.json()
    return response.json()


def move_human_to_cpu_turn(
    client: TestClient,
    state: dict,
) -> dict:
    """人間が合法手を指し、CPUの手番へ進める。"""
    assert state["valid_moves"]

    y, x = state["valid_moves"][0]
    response = client.post(
        "/moves/player",
        json={"y": y, "x": x},
    )

    assert response.status_code == 200, response.json()
    return response.json()


def test_start_human_first(client: TestClient) -> None:
    """人間先攻では黒番の初期盤面を返す。"""
    state = start_pvc(client, "first")

    assert state["human_color"] == BLACK
    assert state["cpu_color"] == WHITE
    assert state["turn"] == BLACK
    assert sum(cell != 0 for row in state["board"] for cell in row) == 4


def test_start_cpu_first(client: TestClient) -> None:
    """人間後攻では黒CPUが初手を指す。"""
    state = start_pvc(client, "second")

    assert state["human_color"] == WHITE
    assert state["cpu_color"] == BLACK
    assert state["turn"] == WHITE

    # 初期の4石にCPU初手の1石を加えて5石
    assert sum(cell != 0 for row in state["board"] for cell in row) == 5

    # セッションから再取得しても状態が維持される
    restored = client.get("/state")
    assert restored.status_code == 200
    assert restored.json() == state


def test_random_order_is_reported(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ランダムで決まった色をAPIが返す。"""
    monkeypatch.setattr(
        service_module,
        "choice",
        lambda colors: WHITE,
    )

    state = start_pvc(client, "random")

    assert state["human_color"] == WHITE
    assert state["cpu_color"] == BLACK

    restored = client.get("/state")
    assert restored.status_code == 200
    assert restored.json()["human_color"] == WHITE


def test_pvp_cannot_select_second(
    client: TestClient,
) -> None:
    """PvPでは人間の先後指定を受け付けない。"""
    response = client.post(
        "/games/start",
        json={
            "mode": "pvp",
            "human_order": "second",
        },
    )

    assert response.status_code == 400


@pytest.mark.parametrize(
    "body",
    [
        {"mode": "invalid"},
        {"mode": "pvc", "human_order": "unknown"},
        {"mode": "pvc", "difficulty": "expert"},
        {"mode": "pvc", "human_order": 123},
    ],
)
def test_invalid_start_request(
    client: TestClient,
    body: dict,
) -> None:
    """不正な設定は422で拒否する。"""
    response = client.post(
        "/games/start",
        json=body,
    )

    assert response.status_code == 422


def test_reset_restores_human_first(
    client: TestClient,
) -> None:
    """リセットで盤面と担当色を初期化する。"""
    start_pvc(client, "second")

    response = client.post("/reset")
    assert response.status_code == 200

    state = response.json()

    assert state["human_color"] == BLACK
    assert state["cpu_color"] == WHITE
    assert state["turn"] == BLACK
    assert state["mode"] == "pvc"
    assert state["difficulty"] == "easy"

    assert sum(cell != 0 for row in state["board"] for cell in row) == 4


def test_black_cpu_analysis(
    client: TestClient,
) -> None:
    """黒CPUの手番で解析できる。"""
    state = start_pvc(client, "second")

    # 人間は白なので、着手後は黒CPUの手番
    state = move_human_to_cpu_turn(client, state)

    assert state["turn"] == BLACK

    response = client.get("/analysis?depth=1")

    assert response.status_code == 200, response.json()

    analysis = response.json()

    assert analysis["best_move"] is not None
    assert analysis["nodes_visited"] > 0
    assert analysis["candidates"]

    # 解析結果は現在のCPUの合法手に含まれる
    assert analysis["best_move"] in state["valid_moves"]


def test_black_cpu_analysis_token(
    client: TestClient,
) -> None:
    """黒CPUの解析済み着手を実際に反映できる。"""
    state = start_pvc(client, "second")
    state = move_human_to_cpu_turn(client, state)

    analysis_response = client.get("/analysis")
    assert analysis_response.status_code == 200

    analysis = analysis_response.json()
    token = analysis["analysis_token"]

    assert isinstance(token, str)
    assert token

    # 解析トークンに黒CPUの色が記録されている
    verified = othello.analysis_tokens.verify(token)
    assert verified.cpu_color == BLACK

    response = client.post(
        "/moves/cpu",
        json={"analysis_token": token},
    )

    assert response.status_code == 200, response.json()

    after = response.json()
    y, x = analysis["best_move"]

    assert after["board"][y][x] == BLACK
    assert after["human_color"] == WHITE
    assert after["cpu_color"] == BLACK


def test_wrong_cpu_color_token_rejected(
    client: TestClient,
) -> None:
    """異なる担当色で署名された解析結果を拒否する。"""
    state = start_pvc(client, "second")
    state = move_human_to_cpu_turn(client, state)

    response = client.get("/analysis")
    assert response.status_code == 200

    valid_token = response.json()["analysis_token"]
    assert isinstance(valid_token, str)

    verified = othello.analysis_tokens.verify(valid_token)

    # 同じ盤面だが、CPU色だけを白にしたトークン
    wrong_color_token = othello.analysis_tokens.issue(
        game_id=verified.game_id,
        board=state["board"],
        version=verified.version,
        difficulty=verified.difficulty,
        depth=verified.depth,
        move=verified.move,
        cpu_color=WHITE,
    )

    move_response = client.post(
        "/moves/cpu",
        json={"analysis_token": wrong_color_token},
    )

    assert move_response.status_code == 409


def test_analysis_token_rejected_after_reset(
    client: TestClient,
) -> None:
    """リセット後に古い解析トークンを利用できない。"""
    state = start_pvc(client, "second")
    move_human_to_cpu_turn(client, state)

    response = client.get("/analysis")
    assert response.status_code == 200

    token = response.json()["analysis_token"]
    assert isinstance(token, str)

    assert client.post("/reset").status_code == 200

    result = client.post(
        "/moves/cpu",
        json={"analysis_token": token},
    )

    assert result.status_code == 409


def test_openapi_includes_start_endpoint(
    client: TestClient,
) -> None:
    """OpenAPIに新しい対局開始APIが登録されている。"""
    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]
    assert "/games/start" in paths
    assert "post" in paths["/games/start"]
