from flask.testing import FlaskClient
import app as othello

def test_index(client: FlaskClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "オセロ" in response.get_data(as_text=True)

def test_static_files(client: FlaskClient) -> None:
    # CSS・JavaScriptが配信される
    assert client.get("/static/css/style.css").status_code == 200
    assert client.get("/static/js/othello.js").status_code == 200

def test_initial_state(client: FlaskClient) -> None:
    # -1, -1で盤面取得
    response = client.post("/click", json={
        "y": -1, "x": -1, "mode": "pvp"
    })
    print("STATUS:", response.status_code)
    print("RESPONSE", response.get_json())
    data = response.get_json()
    assert response.status_code == 200

def test_valid_move(client: FlaskClient) -> None:
    # PvPで黒の合法手を実行
    response = client.post("/click", json={
        "y": 2, "x": 3, "mode": "pvp"
    })
    data = response.get_json()
    assert response.status_code == 200
    assert data["board"][2][3] == 1
    assert data["board"][3][3] == 1
    assert data["turn"] == 2

def test_reset(client: FlaskClient) -> None:
    # 着手後にリセットする
    client.post("/click", json={
        "y": 2, "x": 3, "mode": "pvp"
    })
    response = client.post("/reset", json={})
    data = response.get_json()
    assert response.status_code == 200
    assert data["turn"] == 1
    assert sum(row.count(1) for row in data["board"]) == 2
    assert sum(row.count(2) for row in data["board"]) == 2

def test_invalid_coordinates(client: FlaskClient) -> None:
    # 範囲外の座標を拒否する
    response = client.post("/click", json={
        "y": 100, "x": 3, "mode": "pvp"
    })
    assert response.status_code == 400

def test_invalid_json(client: FlaskClient) -> None:
    # JSONオブジェクトではない入力を拒否する
    response = client.post("/click", json=[1, 2, 3])
    assert response.status_code == 400

def test_illegal_move(client: FlaskClient) -> None:
    # 初期盤面の角には置けない
    response = client.post("/click", json={
        "y": 0, "x": 0, "mode": "pvp"
    })
    assert response.status_code == 400

def test_cpu_game(client: FlaskClient, monkeypatch) -> None:
    # CPUが予測可能な合法手を選ぶよう差し替える
    # Minimax自体のテストはtest_cpu.pyが担当
    monkeypatch.setattr(
        othello, "choose_cpu_move",
        lambda board: (2, 2)
    )
    # まず黒が(2,3)に置く
    response = client.post("/click", json={
        "y": 2, "x": 3, "mode": "pvc"
    })
    data = response.get_json()
    assert response.status_code == 200
    # CPUが白石を置いたことを確認
    assert data["board"][2][2] == 2
    assert data["turn"] == 1
    assert data["mode"] == "pvc"

def test_mode_change_after_move(client: FlaskClient) -> None:
    # 着手後にモードを変更できない
    client.post("/click", json={
        "y": 2, "x": 3, "mode": "pvp"
    })
    response = client.post("/click", json={
        "y": -1, "x": -1, "mode": "pvc"
    })
    assert response.status_code == 409