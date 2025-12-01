from synaplex.cognition.manifolds import ManifoldStore, ManifoldEnvelope
from synaplex.core.ids import AgentId


def test_manifold_store_roundtrip():
    store = ManifoldStore()
    agent_id = AgentId("agent-1")

    assert store.load_latest(agent_id) is None

    env = ManifoldEnvelope(
        agent_id=agent_id,
        version=1,
        content="secret-internal-worldview",
        metadata={},
    )
    store.save(env)

    loaded = store.load_latest(agent_id)
    assert loaded is not None
    assert loaded.agent_id == agent_id
    assert loaded.content == "secret-internal-worldview"


def test_manifold_not_accessible_via_core_or_worlds():
    """
    Sanity check: ManifoldEnvelope is not re-exported from core or worlds,
    which helps prevent casual misuse and keeps manifolds cognitively scoped.
    """
    import synaplex.core as core
    import synaplex.worlds.fractalmesh as fm

    # These modules should not expose ManifoldEnvelope symbols.
    assert not hasattr(core, "ManifoldEnvelope")
    assert not hasattr(fm, "ManifoldEnvelope")

