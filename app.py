import os
import secrets

from flask import Flask, jsonify, render_template, request, session

from storage import GameRecord, GameStore
from service import GameError, GameService

app = Flask(__name__)

app.secret_key = (
    os.environ.get("FLASK_SECRET_KEY")
    or secrets.token_hex(32)
)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

store = GameStore()

def get_game() -> GameRecord:
    game_id = session.get("game_id")
    if isinstance(game_id, str):
        record = store.get(game_id)
        if record is not None:
            return record
    game_id, record = store.create()
    session["game_id"] = game_id
    return record

@app.errorhandler(GameError)
def handle_game_error(error: GameError):
    return jsonify({"error": str(error)}), error.status_code

@app.route('/', methods=["GET"])
def index():
    get_game()
    return render_template('index.html')

@app.route("/state", methods={"GET"})
def get_state():
    service = GameService(get_game())
    return jsonify(service.state())

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
    service = GameService(record)
    with record.lock:
        service.change_mode(mode)
        if not is_state_request:
            service.play(y, x)
        return jsonify(service.state())

@app.route('/reset', methods = ['POST'])
def handle_reset():
    record = get_game()
    service = GameService(record)
    with record.lock:
        record.game.reset()
        return jsonify(service.state())

if __name__ == '__main__':
    app.run(debug=True, port=5001)    