# tests/test_branching.py

"""
Tests for BranchingStrategy.

Tests:
- Branch generation with different styles
- Consolidation of multiple branches
- Fallback behavior when no LLM
- Integration with Mind reasoning
"""

from synaplex.cognition.branching import BranchingStrategy, BranchOutput
from synaplex.cognition.llm_client import LLMClient


class DummyLLM(LLMClient):
    """Dummy LLM that returns style-specific responses."""
    def __init__(self, responses: dict = None):
        self.responses = responses or {}
        self.call_count = 0

    def complete(self, prompt: str, **kwargs):
        self.call_count += 1
        # Return style-specific response if we can detect it
        if "explorer" in prompt.lower():
            return type("Resp", (), {"text": "Explorer branch: exploring multiple possibilities...", "raw": {}})()
        elif "skeptic" in prompt.lower():
            return type("Resp", (), {"text": "Skeptic branch: questioning assumptions...", "raw": {}})()
        elif "consolidat" in prompt.lower():
            return type("Resp", (), {"text": "Consolidated: integrated explorer and skeptic perspectives", "raw": {}})()
        else:
            return type("Resp", (), {"text": f"Response {self.call_count}", "raw": {}})()


def test_branching_disabled_without_llm():
    """Test that branching returns empty list when no LLM provided."""
    strategy = BranchingStrategy(llm_client=None)

    branches = strategy.run_branches(
        base_prompt="Test prompt",
        context={},
        styles=["explorer", "skeptic"],
    )

    assert branches == []


def test_branch_generation():
    """Test that branches are generated with different styles."""
    llm = DummyLLM()
    strategy = BranchingStrategy(llm_client=llm, default_styles=["explorer", "skeptic"])

    branches = strategy.run_branches(
        base_prompt="Test reasoning prompt",
        context={"tick": 0},
    )

    assert len(branches) == 2
    assert any(b.name == "explorer" for b in branches)
    assert any(b.name == "skeptic" for b in branches)
    
    explorer_branch = next(b for b in branches if b.name == "explorer")
    assert "exploring" in explorer_branch.notes.lower()
    
    skeptic_branch = next(b for b in branches if b.name == "skeptic")
    assert "questioning" in skeptic_branch.notes.lower()


def test_custom_branch_styles():
    """Test using custom branch styles."""
    llm = DummyLLM()
    strategy = BranchingStrategy(llm_client=llm)

    branches = strategy.run_branches(
        base_prompt="Test prompt",
        context={},
        styles=["structuralist", "synthesizer"],
    )

    assert len(branches) == 2
    assert any(b.name == "structuralist" for b in branches)
    assert any(b.name == "synthesizer" for b in branches)


def test_consolidation_without_llm():
    """Test consolidation falls back to concatenation when no LLM."""
    strategy = BranchingStrategy(llm_client=None)

    branches = [
        BranchOutput(name="explorer", notes="Explorer notes", outward={}),
        BranchOutput(name="skeptic", notes="Skeptic notes", outward={}),
    ]

    consolidated = strategy.consolidate(branches)

    assert "Explorer notes" in consolidated
    assert "Skeptic notes" in consolidated


def test_consolidation_with_llm():
    """Test LLM-backed consolidation."""
    llm = DummyLLM()
    strategy = BranchingStrategy(llm_client=llm)

    branches = [
        BranchOutput(name="explorer", notes="Exploring possibilities A, B, C", outward={}),
        BranchOutput(name="skeptic", notes="Questioning if A is valid", outward={}),
    ]

    consolidated = strategy.consolidate(branches)

    # Should use LLM to consolidate
    assert "integrated" in consolidated.lower() or "consolidat" in consolidated.lower()


def test_consolidation_single_branch():
    """Test that single branch consolidation works."""
    llm = DummyLLM()
    strategy = BranchingStrategy(llm_client=llm)

    branches = [
        BranchOutput(name="explorer", notes="Single branch notes", outward={}),
    ]

    consolidated = strategy.consolidate(branches)

    # Single branch: should just return the notes (no LLM call needed)
    assert consolidated == "Single branch notes"


def test_consolidation_with_prior_manifold():
    """Test consolidation includes prior manifold context."""
    llm = DummyLLM()
    strategy = BranchingStrategy(llm_client=llm)

    branches = [
        BranchOutput(name="explorer", notes="New exploration", outward={}),
    ]

    prior_manifold = "Existing worldview with patterns"
    consolidated = strategy.consolidate(
        branches,
        prior_manifold=prior_manifold,
        context={"tick": 1},
    )

    # Should have called LLM (we can't easily verify it used prior_manifold,
    # but we can verify it completed without error)
    assert consolidated


def test_branch_error_handling():
    """Test that branch errors don't break the process."""
    class ErrorLLM(LLMClient):
        def complete(self, prompt: str, **kwargs):
            if "explorer" in prompt.lower():
                raise RuntimeError("Explorer branch failed")
            return type("Resp", (), {"text": "Skeptic notes", "raw": {}})()

    strategy = BranchingStrategy(llm_client=ErrorLLM())

    branches = strategy.run_branches(
        base_prompt="Test",
        context={},
        styles=["explorer", "skeptic"],
    )

    # Should have one successful branch (skeptic)
    assert len(branches) == 1
    assert branches[0].name == "skeptic"


def test_default_styles():
    """Test default branch styles."""
    llm = DummyLLM()
    strategy = BranchingStrategy(
        llm_client=llm,
        default_styles=["explorer", "skeptic", "structuralist"],
    )

    # Should use default styles when not specified
    branches = strategy.run_branches(
        base_prompt="Test",
        context={},
        styles=None,  # Use defaults
    )

    assert len(branches) == 3
    names = {b.name for b in branches}
    assert names == {"explorer", "skeptic", "structuralist"}


def test_consolidation_fallback_on_error():
    """Test consolidation falls back on LLM error."""
    class ErrorLLM(LLMClient):
        def complete(self, prompt: str, **kwargs):
            if "consolidat" in prompt.lower():
                raise RuntimeError("Consolidation failed")
            return type("Resp", (), {"text": "Branch notes", "raw": {}})()

    strategy = BranchingStrategy(llm_client=ErrorLLM())

    branches = [
        BranchOutput(name="a", notes="Notes A", outward={}),
        BranchOutput(name="b", notes="Notes B", outward={}),
    ]

    # Should fall back to concatenation
    consolidated = strategy.consolidate(branches)
    
    assert "Notes A" in consolidated
    assert "Notes B" in consolidated

