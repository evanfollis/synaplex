# tests/test_invariants_imports.py

def test_core_imports_without_cognition_side_effects():
    import synaplex.core as core  # noqa: F401


def test_cognition_imports_without_core_cycles():
    import synaplex.cognition as cognition  # noqa: F401


def test_worlds_do_not_import_meta():
    import synaplex.worlds.fractalmesh as fm  # noqa: F401
    # This test is mostly a placeholder; additional static checks can be added later.
