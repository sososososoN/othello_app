from typing import Annotated, Literal
from pydantic import BaseModel, Field, StrictInt

GameMode = Literal["pvp", "pvc"]

Difficulty = Literal["easy", "normal", "hard"]

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


class GameStateResponse(BaseModel):
    board: BoardSchema
    turn: Literal[0, 1, 2]
    message: str
    mode: GameMode
    difficulty: Difficulty
    valid_moves: list[ValidMove]
