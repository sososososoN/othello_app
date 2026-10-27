from flask import Flask, jsonify, render_template, request

from game import BLACK, WHITE, Game
from cpu import choose_cpu_move

app = Flask(__name__)

current_game = Game()
current_mode = "pvp"

def serialize_game() -> dict:
    return {
        "board": current_game.board,
        "turn": current_game.turn,
        "message": current_game.message,
        "mode": current_mode,
        "valid_moves": [
            [y, x] for y, x in current_game.valid_moves()
        ]
    }

def process_cpu_turn() -> None:
    if current_mode != "pvc":
        return
    while current_game.turn == WHITE:
        move = choose_cpu_move(current_game.board)
        if move is None:
            raise RuntimeError("CPU has no valid move")
        y, x = move
        if not current_game.place(y, x):
            raise RuntimeError("CPU selected an illegal move")

@app.route('/', methods=["GET"])
def index():
    global current_game, current_mode
    current_game = Game()
    current_mode = "pvp"
    return render_template('index.html')

@app.route('/click', methods = ['POST'])
def handle_click():
    global current_mode
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error":"Invalid JSON body"}), 400
    y = data.get("y")
    x = data.get("x")
    mode = data.get("mode", current_mode)
    if type(y) is not int or type(x) is not int:
        return jsonify({"error": "Coordinates must be integers"}), 400
    if mode not in ("pvp", "pvc"):
        return jsonify({"error": "Invalid game mode"}), 400
    is_state_request = y == -1 and x == -1
    if not is_state_request and not (
        0 <= y < 8 and 0 <= x < 8
    ):
        return jsonify({"error": "Coodinates out of range"}), 400
    if mode != current_mode:
        stone_count = sum(
            cell != 0
            for row in current_game.board
            for cell in row
        )
        if stone_count > 4 or current_game.turn == 0:
            return jsonify({"error": "Reset before changing mode"}), 409
        current_mode = mode
    if is_state_request:
        return jsonify(serialize_game())
    if current_mode == "pvc" and current_game.turn == WHITE:
        return jsonify({"error": "It is the CPU's turn"}), 409
    if current_game.turn == 0:
        return jsonify({"error": "Game has ended"}), 409
    if not current_game.place(y, x):
        return jsonify({"error": "Illegal move"}), 400
    process_cpu_turn()
    return jsonify(serialize_game())

@app.route('/reset', methods = ['POST'])
def handle_reset():
    current_game.reset()
    return jsonify(serialize_game())

if __name__ == '__main__':
    app.run(debug=True, port=5001)    