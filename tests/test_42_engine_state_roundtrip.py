from __future__ import annotations

from novel_engine.core.being_engine import BeingEngine



def test_engine_state_roundtrip() -> None:
    engine = BeingEngine()
    state = engine.to_state()

    recovered = BeingEngine()
    recovered.from_state(state)

    recovered_state = recovered.to_state()
    assert recovered_state.model_dump() == state.model_dump()
