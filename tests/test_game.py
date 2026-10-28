from game import BLACK, WHITE, Game


def test_place_and_flip() -> None:
    # 新しいゲームを作る
    game = Game()
    # 黒の合法手を実行
    result = game.place(2, 3)
    # 着手成功と石の反転を確認
    assert result is True
    assert game.board[2][3] == BLACK
    assert game.board[3][3] == BLACK
    # 白に手番が移る
    assert game.turn == WHITE
