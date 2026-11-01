from game import BLACK, WHITE, Board, get_valid_moves

# 盤面の各マスに割り当てる位置評価値
WEIGHTS = (
    (100, -50, 10, 5, 5, 10, -50, 100),
    (-50, -70, 1, 1, 1, 1, -70, -50),
    (10, 1, 3, 2, 2, 3, 1, 10),
    (5, 1, 2, 1, 1, 2, 1, 5),
    (5, 1, 2, 1, 1, 2, 1, 5),
    (10, 1, 3, 2, 2, 3, 1, 10),
    (-50, -70, 1, 1, 1, 1, -70, -50),
    (100, -50, 10, 5, 5, 10, -50, 100),
)

WIN_SCORE = 100_000


def evaluate_board(board: Board) -> int:
    """CPU（白）の視点から盤面を評価する。"""
    black = sum(row.count(BLACK) for row in board)
    white = sum(row.count(WHITE) for row in board)

    black_moves = get_valid_moves(board, BLACK)
    white_moves = get_valid_moves(board, WHITE)

    # 両者に合法手がなければ終局
    if not black_moves and not white_moves:
        difference = white - black
        if difference > 0:
            return WIN_SCORE + difference
        if difference < 0:
            return -WIN_SCORE + difference
        return 0

    stone_count = black + white

    # 終盤は石数差を評価
    if stone_count > 54:
        return white - black

    # マスごとの位置評価
    position_score = 0

    for y, row in enumerate(board):
        for x, cell in enumerate(row):
            if cell == WHITE:
                position_score += WEIGHTS[y][x]
            elif cell == BLACK:
                position_score -= WEIGHTS[y][x]

    # 合法手数の差
    mobility_score = len(white_moves) - len(black_moves)

    corners = (
        (0, 0),
        (0, 7),
        (7, 0),
        (7, 7),
    )

    corner_score = 0

    for y, x in corners:
        if board[y][x] == WHITE:
            corner_score += 1
        elif board[y][x] == BLACK:
            corner_score -= 1

    return position_score + mobility_score * 5 + corner_score * 25
