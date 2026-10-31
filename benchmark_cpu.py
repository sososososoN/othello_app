
from statistics import mean
from time import perf_counter

from cpu import choose_cpu_move
from game import create_board


def benchmark(depth: int, runs: int = 3) -> None:
    board = create_board()
    durations = []

    for _ in range(runs):
        start = perf_counter()

        move = choose_cpu_move(
            board,
            depth=depth,
        )

        elapsed = perf_counter() - start
        durations.append(elapsed)

    print(
        f"depth={depth} "
        f"move={move} "
        f"avg={mean(durations):.4f}s "
        f"min={min(durations):.4f}s "
        f"max={max(durations):.4f}s"
    )


if __name__ == "__main__":
    for depth in (1, 2, 3, 4):
        benchmark(depth)
