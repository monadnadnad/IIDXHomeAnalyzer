from player import Player

def test_player_equals():
    assert Player("DJ", "0000-0000") == Player("DJ", "0000-0000")
    assert Player("DJ2", "1111-1111") == Player("DJ1", "1111-1111")
