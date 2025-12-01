# Branching Strategy Implementation

## Overview

Implemented **Priority 4: Branching Strategy** from the convergence plan. This enables internal multiplicity - allowing minds to explore multiple reasoning paths (conjecture and criticism) and reconcile them into a unified worldview within a single tick.

## What Was Implemented

### 1. Branch Generation with Multiple Styles ✅

**File**: `src/synaplex/cognition/branching.py`

The `BranchingStrategy` now:
- Generates multiple reasoning branches from the same starting point
- Supports multiple branch styles:
  - **explorer**: Generative, divergent, multiple possibilities
  - **skeptic**: Critical, questioning assumptions, finding flaws
  - **structuralist**: Pattern-seeking, organizing principles
  - **synthesizer**: Integrating perspectives, building unified frameworks
- Each branch is an independent LLM reasoning pass
- Branches are ephemeral - they exist only within a single tick

### 2. Consolidation Mechanism ✅

**Key Features**:
- Consolidates multiple branch outputs into unified reasoning
- Treats branches as "prior self-notes" (doesn't reveal branch identities)
- LLM-backed reconciliation that preserves insights from all branches
- Falls back to simple concatenation if no LLM or on error
- Maintains epistemic richness while integrating perspectives

### 3. Integration with Mind ✅

**File**: `src/synaplex/cognition/mind.py`

- Branching is automatically enabled in MANIFOLD mode when LLM is available
- Works seamlessly with the unified loop
- Branches are consolidated before Internal Update
- From the Mind's perspective, history is M₀ → M₁ (not individual branches)

### 4. Configurable Branch Styles ✅

- Default styles: ["explorer", "skeptic"]
- Can specify custom styles per call
- Styles define different cognitive approaches to the same prompt
- Worlds can extend with domain-specific styles

### 5. Error Handling ✅

- Individual branch failures don't break the process
- Consolidation falls back gracefully on errors
- Never breaks the unified loop
- Maintains system stability

## Architectural Compliance

✅ **Internal Multiplicity**:
- Branches are ephemeral - exist only within a tick
- From Mind's perspective: M₀ → M₁, not M₀ → [branches] → M₁
- Branching happens inside Reasoning, not as a separate phase

✅ **Conjecture & Criticism**:
- Explorer = conjecture (generative exploration)
- Skeptic = criticism (questioning, finding flaws)
- Consolidation = reconciliation (integrating perspectives)

✅ **Unified Loop**:
- Branching is part of Reasoning step
- Consolidated output feeds Internal Update
- No new loop phases introduced

✅ **Epistemic Integrity**:
- Branches preserve multiple possibilities
- Consolidation maintains contradictions/tensions when useful
- Not optimized for human consumption

## How It Works

### Branch Generation

1. Mind builds base prompt from percept and manifold
2. BranchingStrategy generates style-specific prompts
3. LLM runs each branch independently
4. Each branch produces BranchOutput with notes

### Consolidation

1. All branch outputs collected
2. Consolidation prompt treats them as "prior self-notes"
3. LLM reconciles them into unified reasoning
4. Result feeds Internal Update as single reasoning trace

### Example Flow

```
Percept → Reasoning:
  ├─ Base Prompt
  ├─ Explorer Branch → "Exploring possibilities A, B, C..."
  ├─ Skeptic Branch → "Questioning if A is valid..."
  └─ Consolidation → "Integrated view: A is promising but needs validation..."
     → Internal Update → M₁
```

## Testing

Created comprehensive tests in `tests/test_branching.py`:

- ✅ Branch generation with different styles
- ✅ Custom branch styles
- ✅ Consolidation with and without LLM
- ✅ Single branch handling
- ✅ Prior manifold context in consolidation
- ✅ Error handling (branch failures, consolidation fallback)
- ✅ Default styles configuration

## Example Usage

```python
from synaplex.cognition.branching import BranchingStrategy
from synaplex.cognition.llm_client import LLMClient

llm = OpenAILLMClient()
strategy = BranchingStrategy(
    llm_client=llm,
    default_styles=["explorer", "skeptic"],
)

# Generate branches
branches = strategy.run_branches(
    base_prompt="Reason about the percept...",
    context={"tick": 0, "percept": ...},
    styles=["explorer", "skeptic"],
)

# Consolidate
consolidated = strategy.consolidate(
    branches=branches,
    prior_manifold="Existing worldview...",
    context={"tick": 0},
)
```

## Impact

This implementation enables:

✅ **Internal Multiplicity**:
- Minds can explore multiple reasoning paths simultaneously
- No premature convergence
- Maintains manifold awareness (multiple possibilities)

✅ **Conjecture & Criticism**:
- Explorer generates possibilities
- Skeptic challenges assumptions
- Consolidation reconciles perspectives

✅ **Research Capability**:
- Study how different reasoning styles affect worldview evolution
- Observe how branches are reconciled
- Experiment with different branch configurations

✅ **Cognitive Richness**:
- More nuanced reasoning than single-pass
- Preserves epistemic diversity
- Maintains contradictions/tensions when useful

## Design Decisions

1. **Branches are Ephemeral**:
   - Exist only within Reasoning step
   - Not persisted individually
   - History is M₀ → M₁, not branch-level

2. **Consolidation Hides Branch Identities**:
   - Treats branches as "prior self-notes"
   - Doesn't tell consolidation "merge explorer and skeptic"
   - Allows natural reconciliation

3. **Optional Branching**:
   - Disabled by default if no LLM
   - Can be disabled by passing None
   - Falls back to single-pass reasoning

4. **Error Resilience**:
   - Individual branch failures don't break process
   - Consolidation fallback on error
   - Never breaks unified loop

## Next Steps

With branching complete, remaining priorities:

1. **Priority 5**: Add manifold persistence (file-based storage)
2. **Priority 2**: Enhance projection creation with richer state views
3. **Priority 6**: Create comprehensive multi-agent examples

## Files Modified

- `src/synaplex/cognition/branching.py` - Complete rewrite with LLM integration
- `src/synaplex/cognition/mind.py` - Integrated branching into reasoning
- `tests/test_branching.py` - Comprehensive test suite

## Key Architectural Points

- **Branches are internal to Reasoning**: Not a separate loop phase
- **Consolidation feeds Update**: Unified reasoning trace goes to Internal Update
- **Preserves Multiplicity**: Not premature convergence
- **Epistemic Integrity**: For agent's future self, not humans

The branching strategy is now fully functional and enables minds to engage in internal conjecture and criticism while maintaining the unified loop architecture.

