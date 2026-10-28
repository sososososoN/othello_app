
from flask.testing import FlaskClient

import app as othello
from game import BLACK, WHITE, Game


def test_clients_have_independent_games(
    client: FlaskClient,
) -> None:
    with othello.app.test_client() as second_client:
        response = client.post("/click", json={
            "y": 2, "x": 3, "mode": "pvp"
        })
        assert response.status_code == 200

        state_a = client.get("/state").get_json()
        state_b = second_client.get("/state").get_json()

        assert state_a["turn"] == WHITE
        assert state_b["turn"] == BLACK
        assert state_b["board"] == Game().board


def test_refresh_preserves_game(client: FlaskClient) -> None:
    client.post("/click", json={
        "y": 2, "x": 3, "mode": "pvp"
    })

    before = client.get("/state").get_json()
    response = client.get("/")
    after = client.get("/state").get_json()

    assert response.status_code == 200
    assert before["board"] == after["board"]
    assert after["turn"] == WHITE


def test_reset_does_not_affect_other_client(
    client: FlaskClient,
) -> None:
    with othello.app.test_client() as second_client:
        for browser in (client, second_client):
            response = browser.post("/click", json={
                "y": 2, "x": 3, "mode": "pvp"
            })
            assert response.status_code == 200

        client.post("/reset", json={})

        state_a = client.get("/state").get_json()
        state_b = second_client.get("/state").get_json()

        assert state_a["board"] == Game().board
        assert state_b["board"] != Game().board


def test_state_does_not_change_board(
    client: FlaskClient,
) -> None:
    before = client.get("/state").get_json()
    after = client.get("/state").get_json()

    assert before["board"] == after["board"]
    assert before["turn"] == after["turn"]


def test_reset_preserves_mode(client: FlaskClient) -> None:
    response = client.post("/click", json={
        "y": -1, "x": -1, "mode": "pvc"
    })
    assert response.status_code == 200

    response = client.post("/reset", json={})
    assert response.status_code == 200
    assert response.get_json()["mode"] == "pvc"
