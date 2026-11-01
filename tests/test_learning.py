from fastapi.testclient import TestClient

from learning.articles import get_article, list_articles, render_article


def test_article_registry() -> None:
    articles = list_articles()
    assert len(articles) >= 1
    assert get_article("minimax") is not None
    assert get_article("unknown") is None


def test_minimax_markdown_rendering() -> None:
    content = render_article("minimax")

    assert content is not None
    assert "<h1>Minimax法とは？</h1>" in content
    assert "ゲーム木" in content


def test_unknown_article_cannot_be_rendered() -> None:
    assert render_article("unknown") is None
    assert render_article("../app") is None


def test_learning_index(client: TestClient) -> None:
    response = client.get("/learn")

    assert response.status_code == 200
    assert "オセロで学ぶAIアルゴリズム" in response.text
    assert "/learn/minimax" in response.text


def test_minimax_article(client: TestClient) -> None:
    response = client.get("/learn/minimax")

    assert response.status_code == 200
    assert "Minimax法とは？" in response.text
    assert 'id="minimax-result"' in response.text
    assert "minimax-demo.js" in response.text


def test_unknown_article_returns_404(client: TestClient) -> None:
    response = client.get("/learn/unknown")

    assert response.status_code == 404


def test_existing_game_remains_available(client: TestClient) -> None:
    response = client.get("/state")

    assert response.status_code == 200
    assert response.json()["turn"] == 1
