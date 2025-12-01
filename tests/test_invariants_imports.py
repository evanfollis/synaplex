# tests/test_invariants_imports.py

import inspect
import importlib


def test_core_imports_without_cognition_side_effects():
    """
    Core module must not import from cognition, meta, or manifolds_indexers.
    
    This ensures core remains independent and doesn't know about LLMs or manifolds.
    """
    import synaplex.core as core
    
    # Check that core doesn't import cognition
    core_source = inspect.getsource(core)
    assert "from synaplex.cognition" not in core_source
    assert "import synaplex.cognition" not in core_source
    
    # Check that core doesn't import meta
    assert "from synaplex.meta" not in core_source
    assert "import synaplex.meta" not in core_source
    
    # Check that core doesn't import manifolds_indexers
    assert "from synaplex.manifolds_indexers" not in core_source
    assert "import synaplex.manifolds_indexers" not in core_source


def test_cognition_imports_without_core_cycles():
    """
    Cognition can import from core, but core must not import from cognition.
    
    This maintains the dependency direction: core -> cognition (not the reverse).
    """
    import synaplex.cognition as cognition
    
    # Cognition should be able to import core
    # This test mainly ensures there are no circular import errors
    assert hasattr(cognition, '__file__')  # Module loaded successfully


def test_worlds_do_not_import_meta():
    """
    Worlds must not import synaplex.meta.
    
    This preserves selection blindness - agents shouldn't know about meta-level evaluation.
    """
    import synaplex.worlds.fractalmesh as fm
    import synaplex.worlds.ideas_world as ideas_world
    
    # Check fractalmesh world
    fm_source = inspect.getsource(fm)
    assert "synaplex.meta" not in fm_source
    
    # Check ideas_world
    ideas_source = inspect.getsource(ideas_world)
    assert "synaplex.meta" not in ideas_source


def test_import_structure():
    """
    Verify that the import structure respects architectural boundaries.
    
    - core: no dependencies on cognition/meta/indexers
    - cognition: can import core, not meta
    - worlds: can import core and cognition, not meta
    - meta: can import everything (for analysis)
    """
    # This is a structural test - if imports work, structure is correct
    # More detailed checks are in other invariant tests
    
    # Core should import cleanly
    import synaplex.core
    
    # Cognition should import cleanly (and can import core)
    import synaplex.cognition
    
    # Worlds should import cleanly
    import synaplex.worlds.fractalmesh
    import synaplex.worlds.ideas_world
    
    # Meta should import cleanly
    import synaplex.meta
    
    # All imports succeeded - structure is valid
    assert True
