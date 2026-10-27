from dataclasses import dataclass, field
from threading import RLock
from uuid import uuid4
from game import Game

@dataclass
class GameRecord:
    game: Game = field(default_factory=Game)
    mode: str = "pvp"
    lock: RLock = field(default_factory=RLock)
    
class GameStore:
    def __init__(self) -> None:
        self._records: dict[str, GameRecord] = {}
        self._lock = RLock()
        
    def create(self) -> tuple[str, GameRecord]:
        with self._lock:
            game_id = uuid4().hex
            record = GameRecord()
            self._records[game_id] = record
            return game_id, record
        
    def get(self, game_id: str) -> GameRecord | None:
        with self._lock:
            return self._records.get(game_id)
        
    def delete(self, game_id: str) -> bool:
        with self._lock:
            if game_id not in self._records:
                return False
            del self._records[game_id]
            return True
        
    def count(self) -> int:
        with self._lock:
            return len(self._records)