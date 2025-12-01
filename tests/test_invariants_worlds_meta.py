import inspect
import synaplex.worlds.fractalmesh as fm


def test_worlds_do_not_import_meta():
    """
    Worlds must not import synaplex.meta.

    This is a lightweight structural check to guard against accidental violations
    of selection blindness.
    """
    source = inspect.getsource(fm)
    assert "synaplex.meta" not in source

