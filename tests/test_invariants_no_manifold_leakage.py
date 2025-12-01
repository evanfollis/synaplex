# tests/test_invariants_no_manifold_leakage.py

from synaplex.core.messages import Percept
from synaplex.core.ids import AgentId
from synaplex.core.messages import Projection, Signal

def test_percept_payloads_are_structured():
    a = AgentId("a")
    b = AgentId("b")

    proj = Projection(id=None, sender=a, receiver=b, payload={"foo": 1})
    sig = Signal(id=None, sender=a, payload={"bar": 2})
    percept = Percept(agent_id=b, tick=0, projections=[proj], signals=[sig])

    ctx = percept.to_context()
    # dumb but useful: ensure no obvious manifold-ish keys
    forbidden_keys = {"manifold", "manifold_text", "worldview"}
    def walk(obj):
        if isinstance(obj, dict):
            assert not (forbidden_keys & set(obj.keys()))
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
    walk(ctx)
