# Synaplex Convergence Plan

This document outlines prioritized steps to converge the codebase with the architecture described in the docs.

## Priority 1: Implement Runtime Message Routing ⚠️ CRITICAL

**Status**: `InProcessRuntime._build_percept()` is a stub (line 65-67)

**What's Missing**:
- No projection gathering from subscribed agents
- No signal collection/filtering via lenses
- No EnvState integration in percepts
- No handling of outward behavior from `act()`

**Implementation Steps**:

1. **Add DNA/Lens storage to runtime**
   - Runtime needs to track DNA per agent (for subscriptions)
   - Runtime needs to track Lenses per agent (for signal filtering)

2. **Implement `_build_percept()` properly**:
   ```python
   def _build_percept(self, agent_id: AgentId, tick_id: int) -> Percept:
       # 1. Get agent's DNA (subscriptions) and Lens
       # 2. Gather projections from subscribed publishers
       # 3. Collect signals from all agents, filter via lens
       # 4. Include relevant EnvState views
       # 5. Return structured Percept
   ```

3. **Handle outward behavior in `tick()`**:
   - Extract signals from `act()` output
   - Extract env_updates and apply to EnvState
   - Store requests for next tick's projection gathering

**Files to Modify**:
- `src/synaplex/core/runtime_inprocess.py` - implement routing
- `src/synaplex/core/runtime_interface.py` - may need DNA/Lens storage interface

**Tests Needed**:
- Test percept construction with subscriptions
- Test signal filtering via lenses
- Test EnvState updates from act() output

---

## Priority 2: Wire Up Projection Creation

**Status**: No mechanism for agents to create projections from their state

**What's Missing**:
- Agents can't expose structured views of their state
- No projection handler in AgentInterface
- No way to respond to requests

**Implementation Steps**:

1. **Add projection handler to AgentInterface**:
   ```python
   def create_projection(self, request: Request) -> Projection:
       """Create a projection in response to a request."""
   ```

2. **Implement in Mind class**:
   - Extract relevant EnvState data
   - Apply receiver's lens transformation
   - Return structured Projection

3. **Update runtime to call projection handlers**:
   - When building percept, call `create_projection()` for each subscription
   - Pass receiver's lens to sender

**Files to Modify**:
- `src/synaplex/core/agent_interface.py` - add projection method
- `src/synaplex/cognition/mind.py` - implement projection creation
- `src/synaplex/core/runtime_inprocess.py` - call projection handlers

---

## Priority 3: Implement Update Mechanism

**Status**: `UpdateMechanism.update_worldview()` is skeleton (just wraps notes)

**What's Missing**:
- No LLM call to integrate prior manifold with new reasoning
- No checkpoint ritual that preserves worldview continuity
- No handling of contradictions/tensions

**Implementation Steps**:

1. **Add LLMClient to UpdateMechanism**:
   - UpdateMechanism needs access to LLM for checkpoint ritual
   - Build prompt that integrates prior + new evidence

2. **Implement proper checkpoint prompt**:
   - Include prior manifold content
   - Include new reasoning notes
   - Ask LLM to update worldview (not summarize for humans)

3. **Handle versioning and metadata**:
   - Track what changed
   - Preserve important tensions/contradictions

**Files to Modify**:
- `src/synaplex/cognition/update.py` - implement LLM-backed update
- May need to pass LLMClient to UpdateMechanism constructor

**Tests Needed**:
- Test manifold versioning
- Test that prior content influences new content
- Test that contradictions are preserved when useful

---

## Priority 4: Implement Branching Strategy

**Status**: `BranchingStrategy` is skeleton (returns empty list)

**What's Missing**:
- No actual branch generation (explorer, skeptic, etc.)
- No consolidation logic
- Not wired into Mind.reason()

**Implementation Steps**:

1. **Implement branch generation**:
   - Create multiple prompt variants (explorer, skeptic, structuralist)
   - Call LLM for each branch
   - Return list of BranchOutput

2. **Implement consolidation**:
   - Take all branch notes
   - Call LLM to reconcile/merge
   - Return single consolidated text

3. **Wire into Mind**:
   - In `_run_reasoning_with_manifold()`, call branching if enabled
   - Pass consolidated result to UpdateMechanism

**Files to Modify**:
- `src/synaplex/cognition/branching.py` - implement branch generation
- `src/synaplex/cognition/mind.py` - wire branching into reasoning

---

## Priority 5: Add Manifold Persistence

**Status**: `ManifoldStore` is in-memory only

**What's Missing**:
- No file-based persistence
- No database option
- Manifolds lost on restart

**Implementation Steps**:

1. **Create FileManifoldStore**:
   - Store manifolds as files (one per agent, versioned)
   - Load latest version on startup
   - Support multiple storage backends

2. **Add persistence path configuration**:
   - Allow worlds to specify storage location
   - Default to in-memory for tests

**Files to Create/Modify**:
- `src/synaplex/cognition/manifolds.py` - add FileManifoldStore
- Or create `src/synaplex/cognition/storage.py`

---

## Priority 6: Create Working Multi-Agent Example

**Status**: Only single-agent smoke test exists

**What's Missing**:
- No example of 2+ agents interacting
- No demonstration of projections/signals
- No end-to-end workflow

**Implementation Steps**:

1. **Create example with 2-3 agents**:
   - Agent A subscribes to Agent B
   - Agent B emits signals
   - Show projection flow

2. **Add integration test**:
   - Run multiple ticks
   - Verify projections are received
   - Verify manifolds evolve differently

**Files to Create**:
- `examples/multi_agent_example.py`
- `tests/test_multi_agent_interaction.py`

---

## Priority 7: Add Tools System

**Status**: DNA has `tools` field but no tool invocation

**What's Missing**:
- No tool registry
- No tool calling in reasoning
- Tools not wired into Mind

**Implementation Steps**:

1. **Create tool registry**:
   - Map tool names to callable functions
   - Tools return structured data (not text)

2. **Wire tools into Mind.reason()**:
   - Check DNA for available tools
   - Make tools available to LLM prompt
   - Handle tool results

**Files to Modify**:
- `src/synaplex/cognition/tools.py` - implement tool registry
- `src/synaplex/cognition/mind.py` - wire tools into reasoning

---

## Priority 8: Enhance EnvState

**Status**: EnvState is minimal key-value store

**What's Missing**:
- No structured views/querying
- No data feed abstraction
- No integration with percept construction

**Implementation Steps**:

1. **Add data feed abstraction**:
   - Define DataFeed interface
   - Allow worlds to register feeds
   - Include feeds in percepts

2. **Add structured views**:
   - Allow querying EnvState by pattern
   - Support filtering/transformation

**Files to Modify**:
- `src/synaplex/core/env_state.py` - enhance with feeds/views

---

## Priority 9: Add Indexer World Skeleton

**Status**: Export exists but no indexer world implementation

**What's Missing**:
- No indexer agents
- No embedding/clustering
- No manifold-derived views

**Implementation Steps**:

1. **Create indexer world structure**:
   - Define indexer agent types
   - Implement embedding agent
   - Implement clustering agent

2. **Wire export → indexer → views pipeline**:
   - Export manifolds to snapshots
   - Run indexers on snapshots
   - Write views to EnvState

**Files to Create**:
- `src/synaplex/manifolds_indexers/indexer_world/agents.py` - implement indexers

---

## Priority 10: Add Comprehensive Tests

**Status**: Only invariant tests exist

**What's Missing**:
- No integration tests
- No tests for message routing
- No tests for manifold updates
- No tests for different world modes

**Tests to Add**:

1. **Runtime tests**:
   - Test subscription-based projection flow
   - Test signal filtering
   - Test EnvState updates

2. **Cognition tests**:
   - Test manifold persistence
   - Test update mechanism
   - Test branching/consolidation

3. **World mode tests**:
   - Test GRAPH_ONLY mode (no LLM)
   - Test REASONING_ONLY mode (no manifold)
   - Test MANIFOLD mode (full loop)

4. **Integration tests**:
   - Test 2-agent interaction
   - Test multi-tick evolution
   - Test projection/signal flow

---

## Quick Wins (Low Effort, High Value)

1. **Add DNA storage to runtime** - Simple dict mapping AgentId → DNA
2. **Add Lens storage to runtime** - Simple dict mapping AgentId → Lens  
3. **Implement basic signal collection** - Just gather all signals, filter later
4. **Add EnvState to percepts** - Include full EnvState.data in percept extras
5. **Create minimal multi-agent test** - 2 agents, 1 subscription, verify percept has projection

---

## Implementation Order Recommendation

1. **Week 1**: Priority 1 (Runtime Routing) + Quick Wins
2. **Week 2**: Priority 2 (Projections) + Priority 3 (Update Mechanism)
3. **Week 3**: Priority 4 (Branching) + Priority 6 (Multi-Agent Example)
4. **Week 4**: Priority 5 (Persistence) + Priority 10 (Tests)
5. **Future**: Priorities 7-9 (Tools, EnvState, Indexers)

---

## Notes

- All changes must respect architectural invariants
- Update ARCHITECTURE.md if adding new concepts
- Add tests for any new functionality
- Keep nature/nurture separation strict
- Never leak manifold text into core/worlds

