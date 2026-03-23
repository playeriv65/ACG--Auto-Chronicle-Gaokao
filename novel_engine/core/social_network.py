from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Set

from config import Config

RelationshipType = Literal[
    "陌生人",
    "朋友",
    "死党",
    "竞争对手",
    "暗恋",
    "暧昧",
    "崇拜",
    "嫉妒",
    "师生关系",
    "敌对",
    "小团体成员",
    "室友",
    "同桌",
]

SocialCircleType = Literal["核心圈", "熟人圈", "泛泛之交"]


@dataclass
class Relationship:
    target_name: str
    relationship_type: RelationshipType
    score: int
    trust: int = 0
    intimacy: int = 0
    conflicts: int = 0
    positive_interactions: int = 0
    memories: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "target_name": self.target_name,
            "relationship_type": self.relationship_type,
            "score": self.score,
            "trust": self.trust,
            "intimacy": self.intimacy,
            "conflicts": self.conflicts,
            "positive_interactions": self.positive_interactions,
            "memories": self.memories[:5],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Relationship":
        return cls(
            target_name=data["target_name"],
            relationship_type=data["relationship_type"],
            score=data["score"],
            trust=data.get("trust", 0),
            intimacy=data.get("intimacy", 0),
            conflicts=data.get("conflicts", 0),
            positive_interactions=data.get("positive_interactions", 0),
            memories=data.get("memories", []),
        )


class SocialNetwork:
    def __init__(self):
        self.relationships: Dict[str, Dict[str, Relationship]] = {}
        self.social_circles: Dict[str, Set[str]] = {}
        self.circles_membership: Dict[str, Set[str]] = {}

    def initialize_for_person(self, person_name: str):
        if person_name not in self.relationships:
            self.relationships[person_name] = {}
        if person_name not in self.social_circles:
            self.social_circles[person_name] = set()

    def add_relationship(
        self,
        from_person: str,
        to_person: str,
        relationship_type: RelationshipType = "陌生人",
        initial_score: int = 0,
    ):
        self.initialize_for_person(from_person)
        self.initialize_for_person(to_person)

        self.relationships[from_person][to_person] = Relationship(
            target_name=to_person,
            relationship_type=relationship_type,
            score=initial_score,
        )

    def get_relationship(
        self, from_person: str, to_person: str
    ) -> Optional[Relationship]:
        return self.relationships.get(from_person, {}).get(to_person)

    def get_mutual_relationship_strength(self, person_a: str, person_b: str) -> int:
        rel_a_to_b = self.get_relationship(person_a, person_b)
        rel_b_to_a = self.get_relationship(person_b, person_a)

        if not rel_a_to_b or not rel_b_to_a:
            return 0

        type_weights = {
            "死党": 1.5,
            "暗恋": 1.3,
            "暧昧": 1.4,
            "朋友": 1.2,
            "竞争对手": 1.0,
            "室友": 1.1,
            "同桌": 1.1,
        }

        weight_a = type_weights.get(rel_a_to_b.relationship_type, 1.0)
        weight_b = type_weights.get(rel_b_to_a.relationship_type, 1.0)

        strength = (rel_a_to_b.score * weight_a + rel_b_to_a.score * weight_b) / 2
        return int(max(0, min(200, strength)))

    def update_relationship(
        self,
        from_person: str,
        to_person: str,
        score_delta: int = 0,
        trust_delta: int = 0,
        intimacy_delta: int = 0,
        add_memory: Optional[str] = None,
        is_positive: bool = True,
    ):
        rel = self.get_relationship(from_person, to_person)
        if not rel:
            return

        rel.score = self._clamp_score(rel.score + score_delta)
        rel.trust = self._clamp_metric(rel.trust + trust_delta)
        rel.intimacy = self._clamp_metric(rel.intimacy + intimacy_delta)

        if is_positive:
            rel.positive_interactions += 1
        else:
            rel.conflicts += 1

        if add_memory:
            rel.memories.append(add_memory)
            if len(rel.memories) > 10:
                rel.memories = rel.memories[-10:]

        self._evolve_relationship_type(rel)

    def _clamp_score(self, value: int) -> int:
        return max(Config.RELATION_MIN, min(Config.RELATION_MAX, value))

    def _clamp_metric(self, value: int) -> int:
        return max(0, min(100, value))

    def _evolve_relationship_type(self, rel: Relationship):
        current = rel.relationship_type

        if rel.score >= 80 and rel.intimacy >= 70 and rel.trust >= 70:
            if rel.positive_interactions > 10:
                rel.relationship_type = "死党"
            elif rel.relationship_type == "陌生人":
                rel.relationship_type = "朋友"
        elif rel.score >= 50 and rel.intimacy >= 40:
            if rel.relationship_type == "陌生人":
                rel.relationship_type = "朋友"
        elif rel.score <= -50:
            rel.relationship_type = "敌对"
        elif rel.score <= -20 and rel.conflicts > 3:
            rel.relationship_type = "竞争对手"

        if rel.intimacy >= 80 and rel.trust >= 60:
            if random.random() < 0.3:
                rel.relationship_type = "暗恋" if rel.intimacy < 90 else "暧昧"

    def get_social_circle_type(
        self, from_person: str, to_person: str
    ) -> SocialCircleType:
        strength = self.get_mutual_relationship_strength(from_person, to_person)

        if strength >= 120:
            return "核心圈"
        elif strength >= 60:
            return "熟人圈"
        else:
            return "泛泛之交"

    def get_core_circle(self, person_name: str) -> List[str]:
        core = []
        for target in self.relationships.get(person_name, {}).keys():
            circle_type = self.get_social_circle_type(person_name, target)
            if circle_type == "核心圈":
                core.append(target)
        return core

    def create_social_circle(self, circle_id: str, members: List[str]):
        if len(members) < 2 or len(members) > 6:
            raise ValueError("Social circle must have 2-6 members")

        self.circles_membership[circle_id] = set(members)
        for member in members:
            self.initialize_for_person(member)
            self.social_circles[member].add(circle_id)

            for other_member in members:
                if other_member != member:
                    self._boost_circle_relationship(member, other_member)

    def _boost_circle_relationship(self, from_person: str, to_person: str):
        """Boost relationship for circle members."""
        rel = self.get_relationship(from_person, to_person)
        if rel:
            rel.score = min(100, rel.score + 20)
            if rel.relationship_type == "陌生人":
                rel.relationship_type = "小团体成员"

    def get_shared_circles(self, person_a: str, person_b: str) -> List[str]:
        """Get social circles that both persons belong to."""
        circles_a = self.social_circles.get(person_a, set())
        circles_b = self.social_circles.get(person_b, set())
        return list(circles_a & circles_b)

    def calculate_interest_affinity(
        self, interests_a: List[str], interests_b: List[str]
    ) -> int:
        if not interests_a or not interests_b:
            return 0

        shared = set(interests_a) & set(interests_b)
        return min(50, len(shared) * 15)

    def to_state(self) -> dict:
        return {
            "relationships": {
                person: {target: rel.to_dict() for target, rel in rels.items()}
                for person, rels in self.relationships.items()
            },
            "social_circles": {
                person: list(circles) for person, circles in self.social_circles.items()
            },
            "circles_membership": {
                circle_id: list(members)
                for circle_id, members in self.circles_membership.items()
            },
        }

    def from_state(self, state: dict):
        self.relationships = {
            person: {
                target: Relationship.from_dict(rel_data)
                for target, rel_data in rels.items()
            }
            for person, rels in state.get("relationships", {}).items()
        }
        self.social_circles = {
            person: set(circles)
            for person, circles in state.get("social_circles", {}).items()
        }
        self.circles_membership = {
            circle_id: set(members)
            for circle_id, members in state.get("circles_membership", {}).items()
        }
