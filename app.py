import os
import secrets
from dataclasses import dataclass, field
from threading import RLock
from uuid import uuid4

from flask import Flask, jsonify, render_template, request, session

from game import EMPTY, WHITE, Game
from cpu import choose_cpu_move

app = Flask(__name__)

app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
@dataclass
class GameRecord:
    game: Game = field(default_factory=Game)
    mode: str = "pvp"
    lock: RLock = field(default_factory=RLock)
    
games: dict[str, GameRecord] = {}
registry_lock = RLock()

def get_game() -> GameRecord:
    game_id = session.get("game_id")
    with registry_lock:
        if isinstance(game_id, str) and game_id in games:
            return games[game_id]
        game_id = uuid4().hex
        record = GameRecord()
        games[game_id] = record
        session["game_id"] = game_id
        return record

def serialize_game(record: GameRecord) -> dict:
    return {
        "board": record.game.board,
        "turn": record.game.turn,
        "message": record.game.message,
        "mode": record.mode,
        "valid_moves": [
            [y, x] for y, x in record.game.valid_moves()
        ],
    }

def process_cpu_turn(record: GameRecord) -> None:
    if record.mode != "pvc":
        return
    while record.game.turn == WHITE:
        move = choose_cpu_move(record.game.board)
        if move is None:
            raise RuntimeError("CPU has no valid move")
        y, x = move
        if not record.game.place(y, x):
            raise RuntimeError("CPU selected an illegal move")

@app.route('/', methods=["GET"])
def index():
    get_game()
    return render_template('index.html')

@app.route('/click', methods = ['POST'])
def handle_click():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error":"Invalid JSON body"}), 400
    y = data.get("y")
    x = data.get("x")
    mode = data.get("mode")
    if type(y) is not int or type(x) is not int:
        return jsonify({"error": "Coordinates must be integers"}), 400
    if mode not in ("pvp", "pvc"):
        return jsonify({"error": "Invalid game mode"}), 400
    is_state_request = y == -1 and x == -1
    if not is_state_request and not (
        0 <= y < 8 and 0 <= x < 8
    ):
        return jsonify({"error": "Coodinates out of range"}), 400
    record = get_game()
    with record.lock:
        if mode != record.mode:
            stone_count = sum(
                cell != EMPTY
                for row in record.game.board
                for cell in row
            )
            if stone_count > 4 or record.game.turn == EMPTY:
                return jsonify({
                    "error": "Reset before changing mode"
                    }), 409
            record.mode = mode
        if is_state_request:
            return jsonify(serialize_game(record))
        if record.mode == "pvc" and record.game.turn == WHITE:
            return jsonify({"error": "It is the CPU's turn"}), 409
        if record.game.turn == EMPTY:
            return jsonify({"error": "Game has ended"}), 409
        if not record.game.place(y, x):
            return jsonify({"error": "Illegal move"}), 400
        process_cpu_turn(record)
        return jsonify(serialize_game(record))

@app.route('/reset', methods = ['POST'])
def handle_reset():
    record = get_game()
    with record.lock:
        record.game.reset()
        return jsonify(serialize_game(record))
    
@app.route("/state", methods={"GET"})
def get_state():
    record = get_game()
    with record.lock:
        return jsonify(serialize_game(record))

if __name__ == '__main__':
    app.run(debug=True, port=5001)    