
from fastapi.testclient import TestClient

import app as othello
from game import BLACK, WHITE, Game


def test_clients_have_independent_games(
    client: TestClient,
) -> None:
    second_client = TestClient(othello.app)

    response = client.post(
        "/moves",
        json={"y": 2, "x": 3},
    )

    assert response.status_code == 200

    state_a = client.get("/state").json()
    state_b = second_client.get("/state").json()

    assert state_a["turn"] == WHITE
    assert state_b["turn"] == BLACK
    assert state_b["board"] == Game().board


def test_refresh_preserves_game(
    client: TestClient,
) -> None:
    response = client.post(
        "/moves",
        json={"y": 2, "x": 3},
    )

    assert response.status_code == 200

    before = client.get("/state").json()

    response = client.get("/")
    after = client.get("/state").json()

    assert response.status_code == 200
    assert before["board"] == after["board"]
    assert after["turn"] == WHITE


def test_reset_does_not_affect_other_client(
    client: TestClient,
) -> None:
    second_client = TestClient(othello.app)

    for browser in (client, second_client):
        response = browser.post(
            "/moves",
            json={"y": 2, "x": 3},
        )

        assert response.status_code == 200

    response = client.post("/reset", json={})
    assert response.status_code == 200

    state_a = client.get("/state").json()
    state_b = second_client.get("/state").json()

    assert state_a["board"] == Game().board
    assert state_b["board"] != Game().board


def test_state_does_not_change_board(
    client: TestClient,
) -> None:
    before = client.get("/state").json()
    after = client.get("/state").json()

    assert before["board"] == after["board"]
    assert before["turn"] == after["turn"]


def test_reset_preserves_mode(
    client: TestClient,
) -> None:
    response = client.patch(
        "/mode",
        json={"mode": "pvc"},
    )

    assert response.status_code == 200

    response = client.post("/reset", json={})

    assert response.status_code == 200
    assert response.json()["mode"] == "pvc"
