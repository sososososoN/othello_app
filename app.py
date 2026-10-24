from flask import Flask, render_template, jsonify, request
import random
import copy

app = Flask(__name__)

def create_board():
    board = [[0]*8 for _ in range(8)]
    board[3][3], board[4][4] = 2, 2
    board[3][4], board[4][3] = 1, 1
    return board

DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    ( 0, -1),          ( 0, 1),
    ( 1, -1), ( 1, 0), ( 1, 1)
]

WEIGHTS = [
    [100, -50, 10,  5,  5, 10, -50, 100],
    [-50, -70,  1,  1,  1,  1, -70, -50],
    [ 10,   1,  3,  2,  2,  3,   1,  10],
    [  5,   1,  2,  1,  1,  2,   1,   5],
    [  5,   1,  2,  1,  1,  2,   1,   5],
    [ 10,   1,  3,  2,  2,  3,   1,  10],
    [-50, -70,  1,  1,  1,  1, -70, -50],
    [100, -50, 10,  5,  5, 10, -50, 100],
]

def get_flippable_stones(
    board: list[list[int]],
    y: int,
    x: int,
    player: int,
) -> list[tuple[int, int]]:
    if not (0 <= y < 8 and 0 <= x < 8):
        return []
    if board[y][x] != 0:
        return []
    opponent = 3 - player
    stones_to_flip = []
    for dy, dx in DIRECTIONS:
        candidates = []
        cy, cx = y + dy, x + dx
        while (
            0 <= cy < 8
            and 0 <= cx < 8
            and board[cy][cx] == opponent
        ):
            candidates.append((cy,cx))
            cy += dy
            cx += dx
            if (
                candidates
                and 0 <= cy < 8
                and 0 <= cx < 8
                and board[cy][cx] == player
            ):
                stones_to_flip.extend(candidates)
    return stones_to_flip

def get_valid_moves(board, player):
    moves = []
    for y in range(8):
        for x in range(8):
            if get_flippable_stones(board, y, x, player):
                moves.append([y, x])
    return moves


def has_valid_move(board, player):
    for y in range(8):
        for x in range(8):
            if get_flippable_stones(board, y, x, player):
                return True
    return False   
    
current_game = {
    "board": create_board(),
    "turn": 1,
    "mode": "pvp",
    "message": ""
}

def place_and_flip(y, x):
    player = current_game["turn"]
    flippable = get_flippable_stones(current_game["board"], y, x, player)
    if flippable:
        current_game["board"][y][x] = player
        for fy, fx in flippable:
            current_game["board"][fy][fx] = player
        current_game["turn"] = 3 - player
        next_player = 3 - player
        if has_valid_move(current_game["board"], next_player):
            current_game["turn"] = next_player
            current_game["message"] = ""
        elif has_valid_move(current_game["board"], player):
            current_game["turn"] = player
            current_game["message"] = "相手はパスです"
        else:
            black = sum(row.count(1) for row in current_game["board"])
            white = sum(row.count(2) for row in current_game["board"])
            current_game["turn"] = 0
            current_game["message"] = f"終了！黒:{black} 白:{white}"
        return True
    return False

def get_library(board, y, x):
    library = 0
    for dy, dx in DIRECTIONS:
        cy, cx = y + dy, x + dx
        if 0 <= cy < 8 and 0 <= cx < 8 and board[cy][cx] == 0:
            library += 1
    return library

def evaluate_board_modern(board, turn_count):
    if turn_count > 54:
        black = sum(row.count(1) for row in board)
        white = sum(row.count(2) for row in board)
        return white - black
    score = 0
    for y in range(8):
        for x in range(8):
            if board[y][x] == 0: continue
            cell_score = WEIGHTS[y][x]
            if board[y][x] == 2:
                score += cell_score
            else:
                score -= cell_score
    return score

def cpu_action():
    board = current_game["board"]
    turn_count = sum(row.count(1) + row.count(2) for row in board)
    moves = [(y, x) for y in range(8) for x in range(8) if get_flippable_stones(board, y, x, 2)]
    if not moves:
        current_game["message"] = "白はパス"
        current_game["turn"] = 1
        return
    best_score = -float('inf')
    best_move = moves[0]
    for y, x in moves:
        temp_board = copy.deepcopy(board)
        flippable = get_flippable_stones(temp_board, y, x, 2)
        library_penalty = sum(get_library(temp_board, fy, fx) for fy, fx in flippable)
        temp_board[y][x] = 2
        for fy, fx in flippable:
            temp_board[fy][fx] = 2
        score_depth = 5 if turn_count > 48 else 4
        score = minimax(temp_board, score_depth, -float('inf'), float('inf'), False, turn_count)
        total_eval = score - (library_penalty *2)
        if total_eval > best_score:
            best_score = total_eval
            best_move = (y, x)
    place_and_flip(best_move[0], best_move[1])

def evaluate_board(board):
    score = 0
    for y in range(8):
        for x in range(8):
            if board[y][x] == 2:
                score += WEIGHTS[y][x]
            elif board[y][x] == 1:
                score -= WEIGHTS[y][x]
    return score

def minimax(board, depth, alpha, beta, is_maximizing, turn_count):
    if depth == 0:
        return evaluate_board_modern(board, turn_count)
    player = 2 if is_maximizing else 1
    moves = [(y, x) for y in range(8) for x in range(8) if get_flippable_stones(board, y, x, player)]
    if not moves:
        return evaluate_board_modern(board, turn_count)
    if is_maximizing:
        best_value = -float('inf')
        for y, x in moves:
            temp_board = copy.deepcopy(board)
            flippable = get_flippable_stones(temp_board, y, x, 2)
            temp_board[y][x] = 2
            for fy, fx in flippable:
                temp_board[fy][fx] = 2
            child_value = minimax(temp_board, depth - 1, alpha, beta, False, turn_count)
            best_value = max(best_value, child_value)
            alpha = max(alpha, best_value)
            if alpha >= beta:
                break
        return best_value
    else:
        best_value = float('inf')
        for y, x in moves:
            temp_board = copy.deepcopy(board)
            flippable = get_flippable_stones(temp_board, y, x, 1)
            temp_board[y][x] = 1
            for fy, fx in flippable:
                temp_board[fy][fx] = 1
            child_value = minimax(temp_board, depth - 1, alpha, beta, True, turn_count)
            best_value = min(best_value, child_value)
            beta = min(beta, best_value)
            if beta <= alpha:
                break
        return best_value

@app.route('/')
def index():
    global current_game
    current_game = {
        "board": create_board(),
        "turn": 1,
        "mode": "pvp",
        "message": ""
    }
    return render_template('index.html')

@app.route('/click', methods = ['POST'])
def handle_click():
    data = request.json
    y, x = data.get('y'), data.get('x')
    current_game["mode"] = data.get('mode', 'pvp')
    if y != -1 and current_game["turn"] != 0:
        if current_game["mode"] == "pvc" and current_game["turn"] == 2:
            current_game["valid_moves"] = get_valid_moves(current_game["board"], current_game["turn"])
            return jsonify(current_game)
        if place_and_flip(y, x):
            if current_game["mode"] == "pvc" and current_game["turn"] == 2:
                cpu_action()
    if current_game["turn"] != 0:
        current_game["valid_moves"] = get_valid_moves(current_game["board"], current_game["turn"])
    else:
        current_game["valid_moves"] = []
    return jsonify(current_game)

@app.route('/reset', methods = ['POST'])
def handle_reset():
    current_game["board"] = create_board()
    current_game["turn"] = 1
    current_game["message"] = ""
    current_game["valid_moves"] = get_valid_moves(current_game["board"], current_game["turn"])
    return jsonify(current_game)

if __name__ == '__main__':
    app.run(debug=True, port=5001)    