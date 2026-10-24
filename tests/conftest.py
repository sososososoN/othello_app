import pytest
import app as othello

@pytest.fixture
def client():
    othello.app.config.update(TESTING=True)
    othello.current_game = {
        "board": othello.create_board(),
        "turn": 1,
        "mode": "pvp",
        "message": ""
    }
    with othello.app.test_client() as test_client:
        yield test_client