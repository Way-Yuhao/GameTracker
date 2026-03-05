from __future__ import annotations

import heapq
from dataclasses import dataclass, field


@dataclass
class RelationServer:
    relations: dict[str, set[str]] = field(default_factory=dict)

    def add_friend(self, user1: str, user2: str) -> None:
        if user1 == user2:
            return
        self.relations.setdefault(user1, set()).add(user2)
        self.relations.setdefault(user2, set()).add(user1)

    def delete_friend(self, user1: str, user2: str) -> None:
        self.relations.setdefault(user1, set()).discard(user2)
        self.relations.setdefault(user2, set()).discard(user1)

    def get_friends(self, user: str) -> set[str]:
        return set(self.relations.get(user, set()))


@dataclass
class ScoreServer:
    top_k: int = 10
    scores: dict[str, int] = field(default_factory=dict)
    _top_heap: list[tuple[int, str]] = field(default_factory=list)
    _top_map: dict[str, int] = field(default_factory=dict)

    def update_score(self, user: str, won: bool = True) -> int:
        delta = 1 if won else 0
        new_score = self.scores.get(user, 0) + delta
        self.scores[user] = new_score
        self._update_top_heap(user, new_score)
        return new_score

    def get_score(self, user: str) -> int:
        return self.scores.get(user, 0)

    def get_top_score(self) -> list[tuple[str, int]]:
        return sorted(self._top_map.items(), key=lambda item: (-item[1], item[0]))

    def get_top_score_friend_of(self, user: str, friends: set[str], k: int = 10) -> list[tuple[str, int]]:
        ranked = [(friend, self.scores.get(friend, 0)) for friend in friends if friend != user]
        ranked.sort(key=lambda item: (-item[1], item[0]))
        return ranked[:k]

    def _update_top_heap(self, user: str, score: int) -> None:
        if user in self._top_map:
            self._top_map[user] = score
            heapq.heappush(self._top_heap, (score, user))
            self._trim_heap()
            return

        if len(self._top_map) < self.top_k:
            self._top_map[user] = score
            heapq.heappush(self._top_heap, (score, user))
            self._trim_heap()
            return

        min_item = self._peek_valid_min()
        if min_item is None:
            self._top_map[user] = score
            heapq.heappush(self._top_heap, (score, user))
            self._trim_heap()
            return

        min_score, min_user = min_item
        if score > min_score:
            self._pop_valid_min()
            self._top_map.pop(min_user, None)
            self._top_map[user] = score
            heapq.heappush(self._top_heap, (score, user))
            self._trim_heap()

    def _peek_valid_min(self) -> tuple[int, str] | None:
        while self._top_heap:
            score, user = self._top_heap[0]
            if self._top_map.get(user) == score:
                return score, user
            heapq.heappop(self._top_heap)
        return None

    def _pop_valid_min(self) -> tuple[int, str] | None:
        while self._top_heap:
            score, user = heapq.heappop(self._top_heap)
            if self._top_map.get(user) == score:
                return score, user
        return None

    def _trim_heap(self) -> None:
        while len(self._top_map) > self.top_k:
            min_item = self._pop_valid_min()
            if min_item is None:
                break
            _, min_user = min_item
            self._top_map.pop(min_user, None)


@dataclass
class APIGateway:
    score_server: ScoreServer
    relation_server: RelationServer
    authorized_users: set[str] | None = None

    def update_score(self, user: str, won: bool = True) -> int:
        self._check_auth(user)
        return self.score_server.update_score(user=user, won=won)

    def add_friend(self, user1: str, user2: str) -> None:
        self._check_auth(user1)
        self.relation_server.add_friend(user1=user1, user2=user2)

    def delete_friend(self, user1: str, user2: str) -> None:
        self._check_auth(user1)
        self.relation_server.delete_friend(user1=user1, user2=user2)

    def get_top_score(self) -> list[tuple[str, int]]:
        return self.score_server.get_top_score()

    def get_top_score_friend_of(self, user: str) -> list[tuple[str, int]]:
        self._check_auth(user)
        friends = self.relation_server.get_friends(user)
        return self.score_server.get_top_score_friend_of(user=user, friends=friends, k=10)

    def _check_auth(self, user: str) -> None:
        if self.authorized_users is None:
            return
        if user not in self.authorized_users:
            raise PermissionError(f"user '{user}' is not authorized")
