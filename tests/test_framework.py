import pytest

from game_tracker import APIGateway, RelationServer, ScoreServer


def build_gateway(authorized_users=None):
    return APIGateway(
        score_server=ScoreServer(top_k=10),
        relation_server=RelationServer(),
        authorized_users=authorized_users,
    )


def test_update_score_win_loss():
    gateway = build_gateway()
    assert gateway.update_score("alice", won=True) == 1
    assert gateway.update_score("alice", won=False) == 1
    assert gateway.update_score("alice", won=True) == 2


def test_global_top_10_keeps_highest_scores():
    gateway = build_gateway()

    for i in range(12):
        user = f"user{i}"
        for _ in range(i):
            gateway.update_score(user, won=True)

    top = gateway.get_top_score()
    assert len(top) == 10
    assert top[0] == ("user11", 11)
    assert top[-1] == ("user2", 2)
    assert "user0" not in {name for name, _ in top}
    assert "user1" not in {name for name, _ in top}


def test_friend_top_10_and_delete_friend():
    gateway = build_gateway()

    for friend in ["bob", "carol", "dave"]:
        gateway.add_friend("alice", friend)

    for _ in range(3):
        gateway.update_score("bob", won=True)
    for _ in range(5):
        gateway.update_score("carol", won=True)
    for _ in range(1):
        gateway.update_score("dave", won=True)

    assert gateway.get_top_score_friend_of("alice") == [("carol", 5), ("bob", 3), ("dave", 1)]

    gateway.delete_friend("alice", "carol")
    assert gateway.get_top_score_friend_of("alice") == [("bob", 3), ("dave", 1)]


def test_auth_check_blocks_unauthorized_user():
    gateway = build_gateway(authorized_users={"alice"})
    with pytest.raises(PermissionError):
        gateway.update_score("mallory", won=True)
