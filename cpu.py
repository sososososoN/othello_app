from math import inf

from game import (
    BLACK,
    WHITE,
    EMPTY,
    DIRECTIONS,
    Board,
    Position,
    get_flippable_stones,
    get_valid_moves,
)

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


def apply_move(
    board: Board,
    y: int,
    x: int,
    player: int,
) -> Board:
    new_board = [row.copy() for row in board]
    flippable = get_flippable_stones(board, y, x, player)
    if not flippable:
        raise ValueError("Illegal move")
    new_board[y][x] = player
    for fy, fx in flippable:
        new_board[fy][fx] = player
    return new_board


def evaluate_board(board: Board) -> int:
    black = sum(row.count(BLACK) for row in board)
    white = sum(row.count(WHITE) for row in board)

    if not get_valid_moves(board, BLACK) and not get_valid_moves(board, WHITE):
        difference = white - black
        if difference > 0:
            return WIN_SCORE + difference
        if difference < 0:
            return -WIN_SCORE + difference
        return 0

    if black + white > 54:
        return white - black

    score = 0
    for y, row in enumerate(board):
        for x, cell in enumerate(row):
            if cell == WHITE:
                score += WEIGHTS[y][x]
            elif cell == BLACK:
                score -= WEIGHTS[y][x]

    return score


def count_adjacent_empty_cells(
    board: Board,
    y: int,
    x: int,
) -> int:
    count = 0
    for dy, dx in DIRECTIONS:
        ny, nx = y + dy, x + dx
        if 0 <= ny < 8 and 0 <= nx < 8 and board[ny][nx] == EMPTY:
            count += 1
    return count


def minimax(
    board: Board,
    depth: int,
    alpha: float,
    beta: float,
    player: int,
) -> int:
    if player not in (BLACK, WHITE):
        raise ValueError("Invalid player")
    if depth < 0:
        raise ValueError("Depth must be non-negative")
    if depth == 0:
        return evaluate_board(board)
    moves = get_valid_moves(board, player)
    opponent = 3 - player
    if not moves:
        opponent_moves = get_valid_moves(board, opponent)
        if not opponent_moves:
            return evaluate_board(board)
        return minimax(board, depth - 1, alpha, beta, opponent)
    if player == WHITE:
        best = -inf
        for y, x in moves:
            next_board = apply_move(board, y, x, player)
            value = minimax(
                next_board,
                depth - 1,
                alpha,
                beta,
                opponent,
            )
            best = max(best, value)
            alpha = max(alpha, best)
            if alpha >= beta:
                break
        return int(best)
    best = inf
    for y, x in moves:
        next_board = apply_move(board, y, x, player)
        value = minimax(
            next_board,
            depth - 1,
            alpha,
            beta,
            opponent,
        )
        best = min(best, value)
        beta = min(beta, best)
        if alpha >= beta:
            break
    return int(best)


def choose_cpu_move(
    board: Board,
    depth: int | None = None,
) -> Position | None:
    moves = get_valid_moves(board, WHITE)

    if not moves:
        return None

    stone_count = sum(cell != EMPTY for row in board for cell in row)

    if depth is None:
        depth = 5 if stone_count > 48 else 4

    if depth < 0:
        raise ValueError("Depth must be non-negative")

    best_move = moves[0]
    best_score = -inf

    for y, x in moves:
        flippable = get_flippable_stones(board, y, x, WHITE)

        penalty = sum(count_adjacent_empty_cells(board, fy, fx) for fy, fx in flippable)

        next_board = apply_move(board, y, x, WHITE)

        score = minimax(
            next_board,
            depth,
            -inf,
            inf,
            BLACK,
        )

        total_score = score - penalty * 2

        if total_score > best_score:
            best_score = total_score
            best_move = (y, x)

    return best_move
