# Update Mechanism Implementation

## Overview

Implemented **Priority 3: Update Mechanism with LLM Integration** from the convergence plan. This completes the Internal Update step of the unified cognitive loop, enabling manifolds to evolve meaningfully by integrating prior worldviews with new reasoning.

## What Was Implemented

### 1. LLM-Backed Checkpoint Ritual ✅

**File**: `src/synaplex/cognition/update.py`

The `UpdateMechanism` now:
- Accepts an optional `LLMClient` for checkpoint rituals
- Falls back to simple concatenation when no LLM is provided
- Performs epistemic compression (not human summarization)
- Integrates prior manifold with new reasoning notes

### 2. Checkpoint Prompt Design ✅

**Key Principles**:
- **For the agent's future self**, not humans
- **Preserves contradictions and tensions** when useful
- **Maintains worldview continuity** while allowing evolution
- **Epistemic compression**, not summarization
- **Optimized for future reasoning**, not external readability

The prompt guides the LLM to:
1. Integrate new notes into existing worldview
2. Preserve important structural elements and invariants
3. Maintain contradictions/tensions that might be useful
4. Let go of details that no longer matter
5. Promote vague ideas into explicit scaffolds
6. Note what changed and why

### 3. Versioning and Metadata ✅

- Proper version incrementing (v1 → v2 → v3...)
- Metadata tracking:
  - `source`: "checkpoint-ritual" or "simple-update"
  - `version`: current version number
  - `tick`: tick number when available
- AgentId handling (supports both AgentId objects and strings)

### 4. Integration with Mind ✅

**File**: `src/synaplex/cognition/mind.py`

- `Mind` now passes `llm_client` to `UpdateMechanism`
- Internal Update step properly calls checkpoint ritual
- Works seamlessly with the unified loop

### 5. Error Handling ✅

- Falls back to simple update on LLM errors
- Graceful degradation maintains system stability
- Never breaks the unified loop even if LLM fails

## Architectural Compliance

✅ **Nurture Focus**: 
- Update mechanism is purely about internal worldview evolution
- No manifold content leaks outside the Mind
- Checkpoint ritual is self-directed (for future self)

✅ **Unified Loop**:
- Internal Update is a clear, bounded step
- Only happens in MANIFOLD mode
- Integrates with Perception → Reasoning → Internal Update flow

✅ **Epistemic Integrity**:
- Prompts explicitly forbid human-optimized summaries
- Emphasizes preservation of contradictions/tensions
- Maintains epistemic richness

✅ **LLM Abstraction**:
- Uses `LLMClient` interface, not concrete OpenAI
- Can work with any LLM implementation
- Falls back gracefully when no LLM available

## Testing

Created comprehensive tests in `tests/test_update_mechanism.py`:

- ✅ Simple update without LLM
- ✅ LLM-backed checkpoint ritual
- ✅ Versioning and metadata
- ✅ Prior manifold integration
- ✅ Error handling and fallback
- ✅ AgentId handling (both types)

## Example Usage

```python
from synaplex.cognition.update import UpdateMechanism
from synaplex.cognition.llm_client import LLMClient
from synaplex.cognition.manifolds import ManifoldEnvelope
from synaplex.core.ids import AgentId

# Create mechanism with LLM
llm = OpenAILLMClient()  # or any LLMClient
mechanism = UpdateMechanism(llm_client=llm)

# Initial worldview
reasoning_output = {
    "agent_id": AgentId("agent-1"),
    "notes": "Initial reasoning notes...",
    "context": {"tick": 0},
}

envelope = mechanism.update_worldview(prior=None, reasoning_output=reasoning_output)

# Update existing worldview
prior = envelope
new_reasoning = {
    "agent_id": AgentId("agent-1"),
    "notes": "New insights from tick 1...",
    "context": {"tick": 1},
}

updated = mechanism.update_worldview(prior=prior, reasoning_output=new_reasoning)
# updated.version == 2
# updated.content contains integrated worldview
```

## Impact

This implementation enables:

✅ **Meaningful Manifold Evolution**:
- Manifolds now integrate prior worldview with new insights
- Worldviews evolve while maintaining continuity
- Important patterns and tensions are preserved

✅ **Epistemic Compression**:
- Checkpoint ritual performs compression for future reasoning
- Not human summaries, but optimized for agent's own cognition
- Preserves epistemic richness

✅ **Complete Unified Loop**:
- Internal Update step is now fully functional
- The three-step loop (Perception → Reasoning → Internal Update) works end-to-end
- Manifolds evolve based on agent's own reasoning trajectory

✅ **Research Capability**:
- Can now study how worldviews evolve over time
- Can observe manifold trajectories
- Foundation for nature/nurture experiments

## Next Steps

With the update mechanism complete, the next priorities are:

1. **Priority 4**: Implement BranchingStrategy (explorer, skeptic, etc.)
2. **Priority 5**: Add manifold persistence (file-based storage)
3. **Priority 2**: Enhance projection creation with richer state views

## Files Modified

- `src/synaplex/cognition/update.py` - Complete rewrite with LLM integration
- `src/synaplex/cognition/mind.py` - Pass LLM client to UpdateMechanism
- `tests/test_update_mechanism.py` - Comprehensive test suite

## Key Design Decisions

1. **Optional LLM**: Falls back to simple concatenation if no LLM provided
   - Enables testing without LLM
   - Allows graph-only modes
   - Maintains flexibility

2. **Prompt Philosophy**: Explicitly for agent's future self
   - Matches architecture (epistemic compression, not summaries)
   - Preserves contradictions/tensions
   - Maintains epistemic richness

3. **Error Handling**: Graceful fallback on LLM errors
   - Never breaks the unified loop
   - Maintains system stability
   - Allows continued operation

The update mechanism is now a fully functional checkpoint ritual that respects the architectural principles and enables meaningful worldview evolution.

