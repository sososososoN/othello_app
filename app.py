import os
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from storage import GameRecord, SQLiteGameStore
from service import GameError, GameService
from schemas import (
    MoveRequest,
    ModeRequest,
    DifficultyRequest,
    GameStateResponse,
    AnalysisResponse,
    MoveEvaluationResponse,
)
from learning.articles import get_article, list_articles, render_article
from ai.engine import DIFFICULTY_DEPTH, analyze_cpu_move
from game import WHITE

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Othello API", version="1.0.0")

session_secret_key = os.environ.get("SESSION_SECRET_KEY")
if session_secret_key is None or len(session_secret_key) < 32:
    raise RuntimeError("SESSION_SECRET_KEY must contain at least 32 characters")

app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret_key,
    same_site="lax",
    https_only=False,
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

templates = Jinja2Templates(directory=BASE_DIR / "templates")

db_path = Path(
    os.environ.get(
        "OTHELLO_DB_PATH",
        str(BASE_DIR / "data" / "othello.db"),
    )
)

store = SQLiteGameStore(db_path)


def get_game(request: Request) -> GameRecord:
    game_id = request.session.get("game_id")
    if isinstance(game_id, str):
        record = store.get(game_id)
        if record is not None:
            return record
    game_id, record = store.create()
    request.session["game_id"] = game_id
    return record


@app.exception_handler(GameError)
def handle_game_error(request: Request, error: GameError):
    return JSONResponse(
        status_code=error.status_code,
        content={"error": str(error)},
    )


@app.get("/", include_in_schema=False)
def index(request: Request):
    get_game(request)
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/state", response_model=GameStateResponse)
def get_state(request: Request):
    service = GameService(get_game(request))
    return service.state()


@app.post("/moves", response_model=GameStateResponse)
def create_move(request: Request, data: MoveRequest):
    service = GameService(get_game(request))
    return service.play(data.y, data.x)


@app.post("/moves/player", response_model=GameStateResponse)
def create_player_move(
    request: Request,
    data: MoveRequest,
) -> dict:
    service = GameService(get_game(request))
    return service.play_human(data.y, data.x)


@app.post("/moves/cpu", response_model=GameStateResponse)
def create_cpu_move(request: Request) -> dict:
    service = GameService(get_game(request))
    return service.play_cpu()


@app.get("/analysis", response_model=AnalysisResponse)
def get_analysis(
    request: Request,
    depth: Annotated[
        int | None,
        Query(ge=0, le=5),
    ] = None,
) -> AnalysisResponse:
    record = get_game(request)
    with record.lock:
        if record.mode != "pvc":
            raise HTTPException(
                status_code=409,
                detail="Analysis requires PvC mode",
            )
        if record.game.turn != WHITE:
            raise HTTPException(
                status_code=409,
                detail="It is not CPU's turn",
            )
        board = [row.copy() for row in record.game.board]
        selected_depth = DIFFICULTY_DEPTH[record.difficulty] if depth is None else depth
    result = analyze_cpu_move(
        board,
        depth=selected_depth,
    )
    return AnalysisResponse(
        best_move=result.best_move,
        score=result.score,
        depth=result.depth,
        nodes_visited=result.nodes_visited,
        cutoffs=result.cutoffs,
        elapsed_ms=result.elapsed_ms,
        candidates=[
            MoveEvaluationResponse(
                move=candidate.move,
                minimax_score=candidate.minimax_score,
                penalty=candidate.penalty,
                total_score=candidate.total_score,
            )
            for candidate in result.candidates
        ],
    )


@app.patch("/mode", response_model=GameStateResponse)
def update_mode(request: Request, data: ModeRequest):
    service = GameService(get_game(request))
    return service.change_mode(data.mode)


@app.patch(
    "/difficulty",
    response_model=GameStateResponse,
)
def update_difficulty(
    request: Request,
    data: DifficultyRequest,
):
    service = GameService(get_game(request))
    return service.change_difficulty(data.difficulty)


@app.post("/reset", response_model=GameStateResponse)
def handle_reset(request: Request):
    service = GameService(get_game(request))
    return service.reset()


@app.get("/learn", response_class=HTMLResponse)
def learn_index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="learn_index.html",
        context={"articles": list_articles()},
    )


@app.get("/learn/{slug}", response_class=HTMLResponse)
def learn_article(request: Request, slug: str):
    article = get_article(slug)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")

    content = render_article(slug)
    if content is None:
        raise HTTPException(status_code=404, detail="Article content not found")

    return templates.TemplateResponse(
        request=request,
        name="learn_article.html",
        context={
            "article": article,
            "content": content,
        },
    )
