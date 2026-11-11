import os
from pathlib import Path
from typing import Annotated
from threading import BoundedSemaphore

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from backend.storage import GameRecord, SQLiteGameStore, ConcurrentUpdateError
from backend.service import GameError, GameService
from backend.schemas import (
    MoveRequest,
    ModeRequest,
    DifficultyRequest,
    StartGameRequest,
    GameStateResponse,
    AnalysisResponse,
    MoveEvaluationResponse,
    CpuMoveRequest,
)
from backend.learning.articles import get_article, list_articles, render_article
from backend.ai.engine import DIFFICULTY_DEPTH, analyze_cpu_move
from backend.ai.analysis_token import AnalysisTokenManager, board_fingerprint

BACKEND_DIR = Path(__file__).resolve().parent

PROJECT_ROOT = BACKEND_DIR.parent

FRONTEND_DIST_DIR = PROJECT_ROOT / "frontend" / "dist"

app = FastAPI(title="Othello API", version="1.0.0")

session_secret_key = os.environ.get("SESSION_SECRET_KEY")
if session_secret_key is None or len(session_secret_key) < 32:
    raise RuntimeError("SESSION_SECRET_KEY must contain at least 32 characters")

analysis_tokens = AnalysisTokenManager(session_secret_key)
raw_max_concurrent = os.environ.get("ANALYSIS_MAX_CONCURRENT", "1")
try:
    max_concurrent = int(raw_max_concurrent)
except ValueError as exc:
    raise RuntimeError("ANALYSIS_MAX_CONCURRENT must be a positive integer") from exc
if max_concurrent < 1:
    raise RuntimeError("ANALYSIS_MAX_CONCURRENT must be a positive integer")
analysis_slots = BoundedSemaphore(max_concurrent)

cookie_secure_value = os.environ.get("SESSION_COOKIE_SECURE", "false").lower()
if cookie_secure_value not in ("true", "false"):
    raise RuntimeError("SESSION_COOKIE_SECURE must be true or false")
cookie_secure = cookie_secure_value == "true"

app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret_key,
    same_site="lax",
    https_only=cookie_secure,
)

app.mount(
    "/static",
    StaticFiles(directory=PROJECT_ROOT / "static"),
    name="static",
)

app.mount(
    "/assets",
    StaticFiles(
        directory=FRONTEND_DIST_DIR / "assets",
        check_dir=False,
    ),
    name="frontend-assets",
)

templates = Jinja2Templates(directory=PROJECT_ROOT / "templates")

db_path = Path(
    os.environ.get(
        "OTHELLO_DB_PATH",
        str(PROJECT_ROOT / "data" / "othello.db"),
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


@app.exception_handler(ConcurrentUpdateError)
def handle_concurrent_update(
    request: Request,
    error: ConcurrentUpdateError,
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={
            "error": "Game state was updated by another request",
        },
    )


@app.get("/", include_in_schema=False)
def index(request: Request):
    get_game(request)
    index_file = FRONTEND_DIST_DIR / "index.html"
    if not index_file.is_file():
        raise HTTPException(
            status_code=503,
            detail="React frontend has not been built. Run num run build in frontend/.",
        )
    return FileResponse(index_file, media_type="text/html")


@app.get("/othello-icon.png", include_in_schema=False)
def frontend_icon():
    icon_file = FRONTEND_DIST_DIR / "othello-icon.png"
    if not icon_file.is_file():
        raise HTTPException(
            status_code=404,
            detail="Frontend icon not found",
        )
    return FileResponse(icon_file, media_type="image/png")


@app.get("/state", response_model=GameStateResponse)
def get_state(request: Request):
    service = GameService(get_game(request))
    return service.state()


@app.post("/moves", response_model=GameStateResponse)
def create_move(request: Request, data: MoveRequest):
    service = GameService(get_game(request))
    return service.play(data.y, data.x)


@app.post("/games/start", response_model=GameStateResponse)
def start_game(
    request: Request,
    data: StartGameRequest,
):
    service = GameService(get_game(request))
    return service.start_game(
        mode=data.mode,
        difficulty=data.difficulty,
        human_order=data.human_order,
    )


@app.post("/moves/player", response_model=GameStateResponse)
def create_player_move(
    request: Request,
    data: MoveRequest,
) -> dict:
    service = GameService(get_game(request))
    return service.play_human(data.y, data.x)


@app.post("/moves/cpu", response_model=GameStateResponse)
def create_cpu_move(
    request: Request,
    data: CpuMoveRequest | None = None,
) -> dict:
    record = get_game(request)
    service = GameService(record)
    if data is None or data.analysis_token is None:
        return service.play_cpu()

    try:
        verified = analysis_tokens.verify(data.analysis_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    with record.lock:
        game_id = request.session.get("game_id")
        cpu_color = 3 - record.human_color
        if (
            verified.game_id != game_id
            or verified.board_hash != board_fingerprint(record.game.board)
            or verified.version != record.version
            or verified.difficulty != record.difficulty
            or verified.depth != DIFFICULTY_DEPTH[record.difficulty]
            or verified.cpu_color != cpu_color
            or record.mode != "pvc"
            or record.game.turn != cpu_color
        ):
            raise HTTPException(
                status_code=409,
                detail="Analysis result is no longer valid",
            )
        return service.play_cpu(preselected_move=verified.move)


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
        cpu_color = 3 - record.human_color
        if record.game.turn != cpu_color:
            raise HTTPException(
                status_code=409,
                detail="It is not CPU's turn",
            )
        board = [row.copy() for row in record.game.board]
        version = record.version
        difficulty = record.difficulty

        configured_depth = DIFFICULTY_DEPTH[difficulty]
        selected_depth = configured_depth if depth is None else depth
    if not analysis_slots.acquire(blocking=False):
        raise HTTPException(
            status_code=429,
            detail="Too many concurrent analysis requests",
            headers={"Retry-After": "1"},
        )
    try:
        result = analyze_cpu_move(
            board,
            depth=selected_depth,
            player=cpu_color,
        )
    finally:
        analysis_slots.release()
    token = None

    if result.best_move is not None and selected_depth == configured_depth:
        game_id = request.session.get("game_id")

        if isinstance(game_id, str):
            token = analysis_tokens.issue(
                game_id=game_id,
                board=board,
                version=version,
                difficulty=difficulty,
                depth=selected_depth,
                move=result.best_move,
                cpu_color=cpu_color,
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
        analysis_token=token,
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
