import os
import secrets
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from storage import GameRecord, SQLiteGameStore
from service import GameError, GameService
from schemas import MoveRequest, ModeRequest, DifficultyRequest, GameStateResponse

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
    record = get_game(request)
    service = GameService(record)
    with record.lock:
        service.play(data.y, data.x)
        return service.state()


@app.patch("/mode", response_model=GameStateResponse)
def update_mode(request: Request, data: ModeRequest):
    record = get_game(request)
    service = GameService(record)
    with record.lock:
        service.change_mode(data.mode)
        return service.state()


@app.patch(
    "/difficulty",
    response_model=GameStateResponse,
)
def update_difficulty(
    request: Request,
    data: DifficultyRequest,
):
    record = get_game(request)
    service = GameService(record)

    with record.lock:
        service.change_difficulty(data.difficulty)
        return service.state()


@app.post("/reset", response_model=GameStateResponse)
def handle_reset(request: Request):
    record = get_game(request)
    service = GameService(record)
    with record.lock:
        service.reset()
        return service.state()
