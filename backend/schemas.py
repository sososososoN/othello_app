from typing import Annotated, Literal
from pydantic import BaseModel, Field, StrictInt

GameMode = Literal["pvp", "pvc"]

Difficulty = Literal["easy", "normal", "hard"]

HumanOrder = Literal["first", "second", "random"]

PlayerColor = Literal[1, 2]

Cell = Literal[0, 1, 2]

Coordinate = Annotated[
    StrictInt,
    Field(ge=0, le=7),
]

BoardRow = Annotated[
    list[Cell],
    Field(min_length=8, max_length=8),
]

BoardSchema = Annotated[
    list[BoardRow],
    Field(min_length=8, max_length=8),
]

ValidMove = Annotated[
    list[Coordinate],
    Field(min_length=2, max_length=2),
]


class MoveRequest(BaseModel):
    y: Coordinate
    x: Coordinate


class ModeRequest(BaseModel):
    mode: GameMode


class DifficultyRequest(BaseModel):
    difficulty: Difficulty


class StartGameRequest(BaseModel):
    mode: GameMode
    difficulty: Difficulty = "normal"
    human_order: HumanOrder = "first"


class GameStateResponse(BaseModel):
    board: BoardSchema
    turn: Literal[0, 1, 2]
    message: str
    mode: GameMode
    difficulty: Difficulty
    human_color: PlayerColor = 1
    cpu_color: PlayerColor | None = None
    valid_moves: list[ValidMove]


class MoveEvaluationResponse(BaseModel):
    move: ValidMove
    minimax_score: int
    penalty: int
    total_score: int


class AnalysisResponse(BaseModel):
    best_move: ValidMove | None
    score: int | None
    depth: int
    nodes_visited: int
    cutoffs: int
    elapsed_ms: float
    candidates: list[MoveEvaluationResponse]
    analysis_token: str | None = None


class CpuMoveRequest(BaseModel):
    analysis_token: Annotated[
        str | None,
        Field(min_length=1, max_length=4096),
    ] = None
