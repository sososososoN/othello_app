from pathlib import Path

from fastapi.testclient import TestClient

import backend.app as othello


def test_index_without_build_returns_503(
    client: TestClient,
    monkeypatch,
    tmp_path: Path,
) -> None:
    # 追加：存在するがindex.htmlのないディレクトリを設定
    monkeypatch.setattr(
        othello,
        "FRONTEND_DIST_DIR",
        tmp_path,
    )

    # 追加：Reactがビルドされていない場合のエラーを検証
    response = client.get("/")

    assert response.status_code == 503
    assert "has not been built" in response.json()["detail"]


def test_frontend_icon(
    client: TestClient,
    monkeypatch,
    tmp_path: Path,
) -> None:
    # 追加：テスト用faviconを用意
    icon_file = tmp_path / "othello-icon.png"
    icon_file.write_bytes(b"test-icon")

    monkeypatch.setattr(
        othello,
        "FRONTEND_DIST_DIR",
        tmp_path,
    )

    response = client.get("/othello-icon.png")

    assert response.status_code == 200
    assert response.content == b"test-icon"
    assert response.headers["content-type"] == "image/png"


def test_missing_frontend_icon_returns_404(
    client: TestClient,
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        othello,
        "FRONTEND_DIST_DIR",
        tmp_path,
    )

    response = client.get("/othello-icon.png")

    assert response.status_code == 404
