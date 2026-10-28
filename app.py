import os
import secrets
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from storage import GameRecord, GameStore
from service import GameError, GameService
from schemas import MoveRequest, GameStateResponse

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Othello API", version="1.0.0")

app.add_middleware(
    SessionMiddleware,
    secret_key = (
    os.environ.get("FLASK_SECRET_KEY")
    or secrets.token_hex(32)
    ),
    same_site="lax",
    https_only=False,
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

templates = Jinja2Templates(directory=BASE_DIR /"templates")

store = GameStore()

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

@app.get('/', include_in_schema=False)
def index(request: Request):
    get_game(request)
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

@app.get("/state", response_model=GameStateResponse)
def get_state(request: Request):
    service = GameService(get_game(request))
    return service.state()

@app.post('/click', response_model=GameStateResponse)
def handle_click(request: Request, data: MoveRequest):
    y = data.y
    x = data.x
    mode = data.mode
    is_state_request = (y, x) == (-1, -1)
    if not is_state_request and not (
        0 <= y < 8 and 0 <= x < 8
    ):
        raise HTTPException(
            status_code=400,
            detail="Coordinates out of range",
        )
    record = get_game(request)
    service = GameService(record)
    with record.lock:
        service.change_mode(mode)
        if not is_state_request:
            service.play(y, x)
        return service.state()

@app.post('/reset', response_model=GameStateResponse)
def handle_reset(request: Request):
    record = get_game(request)
    service = GameService(record)
    with record.lock:
        service.reset()
        return service.state()   