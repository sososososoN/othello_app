from dataclasses import dataclass
from pathlib import Path

import markdown

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content" / "algorithms"


@dataclass(frozen=True)
class Article:
    slug: str
    title: str
    description: str
    level: str


ARTICLES: tuple[Article, ...] = (
    Article(
        slug="minimax",
        title="Minimax法とは？",
        description="相手も最善の手を選ぶと仮定して、最適な手を探索する方法",
        level="初級",
    ),
)


def list_articles() -> tuple[Article, ...]:
    return ARTICLES


def get_article(slug: str) -> Article | None:
    return next((article for article in ARTICLES if article.slug == slug), None)


def render_article(slug: str) -> str | None:
    article = get_article(slug)
    if article is None:
        return None

    path = CONTENT_DIR / f"{article.slug}.md"
    source = path.read_text(encoding="utf-8")

    return markdown.markdown(
        source,
        extensions=["fenced_code", "tables"],
        output_format="html",
    )
