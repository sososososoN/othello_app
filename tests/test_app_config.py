import os
import subprocess
import sys
from pathlib import Path

import pytest


# プロジェクトのルートディレクトリ
PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "secret",
    [None, "", "short"],
)
def test_invalid_session_secret_prevents_startup(
    secret: str | None,
    tmp_path: Path,
) -> None:
    # 現在の環境変数をコピーする
    env = os.environ.copy()

    # テスト専用DBを使い、実際の対局データを保護する
    env["OTHELLO_DB_PATH"] = str(tmp_path / "othello.db")

    if secret is None:
        env.pop("SESSION_SECRET_KEY", None)
    else:
        env["SESSION_SECRET_KEY"] = secret

    # 別のPythonプロセスでapp.pyを読み込む
    result = subprocess.run(
        [sys.executable, "-c", "import backend.app"],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    # 設定不備なら起動に失敗する
    assert result.returncode != 0
    assert "SESSION_SECRET_KEY" in result.stderr


def test_valid_session_secret_allows_startup(
    tmp_path: Path,
) -> None:
    env = os.environ.copy()
    env["OTHELLO_DB_PATH"] = str(tmp_path / "othello.db")
    env["SESSION_SECRET_KEY"] = "test-only-" + "a" * 40

    result = subprocess.run(
        [sys.executable, "-c", "import backend.app"],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_secure_session_cookie(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # このテスト専用のSQLiteデータベースを使用する
    monkeypatch.setenv(
        "OTHELLO_DB_PATH",
        str(tmp_path / "secure-cookie.db"),
    )

    # 現在の環境変数名を使ってSecureを有効にする
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "true")

    # import済みのアプリでは環境変数が反映されないため、
    # 別プロセスで確認する
    env = os.environ.copy()
    env["SESSION_SECRET_KEY"] = "test-only-" + "a" * 40

    script = """
from fastapi.testclient import TestClient
from backend.app import app

with TestClient(app) as client:
    response = client.get("/state")
    assert response.status_code == 200
    cookie = response.headers["set-cookie"]
    assert "secure" in cookie.lower().split("; ")
"""

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert result.returncode == 0, result.stderr
