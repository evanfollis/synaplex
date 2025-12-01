# Manifold Persistence Implementation

## Overview

Implemented **Priority 5: Manifold Persistence** from the convergence plan. This enables manifolds to persist across restarts, allowing long-horizon experiments and proper study of worldview evolution over time.

## What Was Implemented

### 1. FileManifoldStore ✅

**File**: `src/synaplex/cognition/manifolds.py`

A new file-based storage implementation that:
- Stores manifolds as JSON files on disk
- Organizes by agent: `root/<agent_id>/v<version>.json`
- Loads latest version automatically
- Persists across process restarts

### 2. Storage Structure ✅

**Layout**:
```
manifolds/
  agent-1/
    v1.json
    v2.json
    v3.json
  agent-2/
    v1.json
    v5.json
```

Each JSON file contains:
- `agent_id`: Agent identifier
- `version`: Version number
- `content`: Manifold content (opaque text)
- `metadata`: Dict of metadata

### 3. Version Management ✅

- **Latest version loading**: Automatically finds and loads highest version
- **Specific version loading**: `load_version(agent_id, version)` helper
- **Version listing**: `list_versions(agent_id)` helper
- Versions stored as `v<number>.json` files

### 4. Backward Compatibility ✅

- **InMemoryManifoldStore**: Still available (renamed from ManifoldStore)
- **Abstract base**: `ManifoldStore` is now abstract interface
- **Default behavior**: Mind defaults to `InMemoryManifoldStore` for tests
- **Easy swap**: Worlds can pass `FileManifoldStore` to Mind constructor

### 5. Robustness Features ✅

- **Atomic writes**: Uses temp file + rename to prevent corruption
- **Corrupted file handling**: Returns None gracefully if file is invalid
- **Agent ID sanitization**: Handles special characters in agent IDs
- **Error recovery**: Continues working even if individual files are corrupted

## Usage

### Basic Usage

```python
from synaplex.cognition.manifolds import FileManifoldStore
from synaplex.cognition.mind import Mind
from synaplex.core.ids import AgentId

# Create file-based store
store = FileManifoldStore(root="manifolds")

# Use with Mind
mind = Mind(
    agent_id=AgentId("agent-1"),
    llm_client=llm_client,
    manifold_store=store,  # Pass file store
)
```

### Loading Specific Versions

```python
store = FileManifoldStore(root="manifolds")

# Load latest
latest = store.load_latest(AgentId("agent-1"))

# Load specific version
v5 = store.load_version(AgentId("agent-1"), 5)

# List all versions
versions = store.list_versions(AgentId("agent-1"))
# Returns: [1, 2, 3, 5, 7]
```

### World Configuration

```python
# In world bootstrap
from synaplex.cognition.manifolds import FileManifoldStore

def bootstrap_world():
    # Use file store for persistence
    store = FileManifoldStore(root="data/manifolds")
    
    mind = Mind(
        agent_id=agent_id,
        llm_client=llm_client,
        manifold_store=store,
    )
    return mind
```

## Architectural Compliance

✅ **Manifold Purity**:
- Files store opaque content (not parsed)
- JSON is just encoding, not interpretation
- Metadata preserved but not schema-enforced

✅ **Agent Isolation**:
- Each agent's manifolds stored separately
- No cross-agent access
- Versioning per-agent

✅ **Persistence Boundaries**:
- Storage is purely mechanical (no semantic compression)
- Content is written verbatim
- No summaries or rewriting

✅ **Interface Compatibility**:
- Same interface as in-memory store
- Drop-in replacement
- Easy to swap implementations

## Testing

Created comprehensive tests in `tests/test_manifold_persistence.py`:

- ✅ Basic save/load
- ✅ Version management (latest, specific, listing)
- ✅ Multiple agents
- ✅ Persistence across store instances
- ✅ Corrupted file handling
- ✅ Agent ID sanitization
- ✅ Atomic writes

## Impact

This implementation enables:

✅ **Long-Horizon Experiments**:
- Manifolds persist across restarts
- Can run experiments over days/weeks
- Study worldview evolution over time

✅ **Research Capability**:
- Access historical manifold versions
- Compare worldviews at different points
- Analyze evolution trajectories

✅ **Production Readiness**:
- Real deployments need persistence
- Can handle restarts gracefully
- Data survives process crashes

✅ **Debugging & Analysis**:
- Inspect manifold files directly
- Version history available
- Can load specific versions for analysis

## Design Decisions

1. **JSON Format**:
   - Human-readable for inspection
   - Easy to parse/debug
   - Can be extended with metadata

2. **Version-Based Files**:
   - Simple to find latest (highest number)
   - Easy to access specific versions
   - Preserves full history

3. **Per-Agent Directories**:
   - Clean organization
   - Easy to find all versions for an agent
   - Scalable to many agents

4. **Atomic Writes**:
   - Prevents corruption on crashes
   - Uses temp file + rename pattern
   - Standard filesystem technique

5. **Backward Compatibility**:
   - InMemoryManifoldStore still default
   - Tests don't need to change
   - Worlds opt-in to persistence

## Future Enhancements

Possible future improvements:

1. **Database Backend**: SQLite or PostgreSQL option
2. **Compression**: Optional gzip for large manifolds
3. **Indexing**: Metadata indexing for fast queries
4. **Backup**: Automated snapshot/backup system
5. **Export**: Bulk export for analysis

## Files Modified

- `src/synaplex/cognition/manifolds.py` - Added FileManifoldStore and base class
- `src/synaplex/cognition/mind.py` - Updated to use InMemoryManifoldStore by default
- `src/synaplex/cognition/__init__.py` - Exported new store types
- `tests/test_manifold_persistence.py` - Comprehensive test suite

## Key Architectural Points

- **Mechanical Storage**: Files are written verbatim, no parsing/modification
- **Opaque Content**: Manifold content remains opaque to storage layer
- **Interface Abstraction**: Store interface allows swapping implementations
- **Backward Compatible**: Existing code continues to work

The manifold persistence system is now fully functional and enables long-horizon experiments with proper data durability.

