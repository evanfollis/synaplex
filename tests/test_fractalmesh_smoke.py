# tests/test_fractalmesh_smoke.py

from synaplex.worlds.fractalmesh.bootstrap import bootstrap_fractalmesh_world

def test_fractalmesh_bootstrap_runs_one_tick():
    runtime = bootstrap_fractalmesh_world()
    # should have at least one agent and tolerate a tick
    assert runtime.get_agents()  # non-empty
    runtime.tick(0)
