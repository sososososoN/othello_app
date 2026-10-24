
from flask.testing import FlaskClient


def test_index(client: FlaskClient) -> None:
    # トップページのHTMLが返る
    response = client.get("/")

    assert response.status_code == 200
    assert "オセロ" in response.get_data(as_text=True)


def test_static_js(client: FlaskClient) -> None:
    # JavaScriptがstaticフォルダから配信される
    response = client.get("/static/js/othello.js")

    assert response.status_code == 200
    assert b"drawBoard" in response.data


def test_static_css(client: FlaskClient) -> None:
    # CSSの配信を確認
    response = client.get("/static/css/style.css")

    assert response.status_code == 200
    assert b"#board" in response.data


def test_initial_state(client: FlaskClient) -> None:
    # 現在の初期盤面を取得
    response = client.post("/click", json={
        "y": -1,
        "x": -1,
        "mode": "pvp",
    })

    assert response.status_code == 200

    data = response.get_json()
    assert data is not None
    assert data["turn"] == 1
    assert len(data["board"]) == 8
    assert len(data["valid_moves"]) == 4


def test_valid_move(client: FlaskClient) -> None:
    # 黒が(2,3)に着手
    response = client.post("/click", json={
        "y": 2,
        "x": 3,
        "mode": "pvp",
    })

    assert response.status_code == 200

    data = response.get_json()
    assert data is not None

    # 石が置かれ、白が黒に変わる
    assert data["board"][2][3] == 1
    assert data["board"][3][3] == 1

    # 次の手番は白
    assert data["turn"] == 2


def test_reset(client: FlaskClient) -> None:
    # 一度着手して盤面を変更
    client.post("/click", json={
        "y": 2,
        "x": 3,
        "mode": "pvp",
    })

    # リセットを実行
    response = client.post("/reset", json={})

    assert response.status_code == 200

    data = response.get_json()
    assert data is not None

    # 初期配置に戻ったことを確認
    assert data["turn"] == 1
    assert sum(row.count(1) for row in data["board"]) == 2
    assert sum(row.count(2) for row in data["board"]) == 2
