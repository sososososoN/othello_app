from dataclasses import dataclass
from itsdangerous import BadSignature, URLSafeTimedSerializer
import hashlib
import json

from game import Position, Board


def board_fingerprint(board: Board) -> str:
    serialized = json.dumps(
        board,
        separators=(",", ":"),
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class VerifiedAnalysisMove:
    game_id: str
    version: int
    difficulty: str
    depth: int
    move: Position
    board_hash: str


class AnalysisTokenManager:
    def __init__(self, secret_key: str) -> None:
        self._serializer = URLSafeTimedSerializer(
            secret_key,
            salt="othello-cpu-analysis-v1",
        )

    def issue(
        self,
        *,
        game_id: str,
        board: Board,
        version: int,
        difficulty: str,
        depth: int,
        move: Position,
    ) -> str:
        return self._serializer.dumps(
            {
                "game_id": game_id,
                "board_hash": board_fingerprint(board),
                "version": version,
                "difficulty": difficulty,
                "depth": depth,
                "move": list(move),
            }
        )

    def verify(self, token: str) -> VerifiedAnalysisMove:
        try:
            data = self._serializer.loads(token, max_age=600)
        except BadSignature:
            raise ValueError("Invalid or expired analysis token")
        if not isinstance(data, dict):
            raise ValueError("Invalid analysis token payload")
        game_id = data.get("game_id")
        board_hash = data.get("board_hash")
        version = data.get("version")
        difficulty = data.get("difficulty")
        depth = data.get("depth")
        move = data.get("move")

        if (
            not isinstance(game_id, str)
            or not game_id
            or not isinstance(board_hash, str)
            or len(board_hash) != 64
            or any(character not in "0123456789abcdef" for character in board_hash)
            or type(version) is not int
            or version < 0
            or difficulty not in ("easy", "normal", "hard")
            or type(depth) is not int
            or depth < 0
            or depth > 5
            or not isinstance(move, list)
            or len(move) != 2
            or any(type(n) is not int or not 0 <= n < 8 for n in move)
        ):
            raise ValueError("Invalid analysis token payload")

        return VerifiedAnalysisMove(
            game_id=game_id,
            board_hash=board_hash,
            version=version,
            difficulty=difficulty,
            depth=depth,
            move=(move[0], move[1]),
        )
