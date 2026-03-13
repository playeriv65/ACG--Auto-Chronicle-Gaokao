from __future__ import annotations

from config import Config
from novel_engine.core.being_engine import BeingEngine
from novel_engine.data.database import EventRecord


def test_social_graph_initialized_in_state() -> None:
    engine = BeingEngine()
    state = engine.to_state()
    assert state.social_graph
    for src, row in state.social_graph.items():
        assert src not in row
        for dst, score in row.items():
            assert state.social_graph[dst][src] == score
            assert Config.RELATION_MIN <= score <= Config.RELATION_MAX


def test_event_updates_relation_and_both_moods(monkeypatch) -> None:
    engine = BeingEngine()
    actor_a = engine.students[0].name
    actor_b = engine.students[1].name

    before_relation = engine.social_graph[actor_a][actor_b]
    person_map = {p.name: p for p in (engine.students + engine.teachers)}
    before_mood_a = person_map[actor_a].mood
    before_mood_b = person_map[actor_b].mood

    monkeypatch.setattr(
        engine,
        "_build_event_placeholders",
        lambda _student: {"p1": actor_a, "p2": actor_b, "p3": actor_a, "p4": actor_b},
    )
    monkeypatch.setattr(
        "novel_engine.core.being_engine.get_random_event",
        lambda _season, placeholders=None: EventRecord(
            description=f"【课间·教室】{actor_a}与{actor_b}发生争执。",
            effect="",
            relation_delta=-4,
            mood_delta=-3,
        ),
    )
    monkeypatch.setattr("random.sample", lambda seq, k: [seq[0]])
    monkeypatch.setattr("random.random", lambda: 1.0)

    logs: list[str] = []
    engine._run_events_and_breakthroughs(abs_week=1, season="ANY", logs=logs)

    after_relation = engine.social_graph[actor_a][actor_b]
    after_mood_a = person_map[actor_a].mood
    after_mood_b = person_map[actor_b].mood

    assert after_relation == before_relation - 4
    assert after_mood_a == max(Config.MIN_MOOD, before_mood_a - 3)
    assert after_mood_b == max(Config.MIN_MOOD, before_mood_b - 3)
    assert logs and logs[0].startswith("【突发】")
