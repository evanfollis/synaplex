# synaplex/__init__.py

"""
Synaplex: a cognitive mesh of LLM-native minds.

This package is organized into the following subpackages:

- synaplex.core
- synaplex.cognition
- synaplex.manifolds_indexers
- synaplex.meta
- synaplex.worlds

Submodules are imported explicitly where needed; we do NOT eagerly
import them here to avoid circular import issues during initialization.
"""

# Keeping this minimal avoids circular imports during test collection.
# Consumers should use explicit imports like:
#   import synaplex.core as core
#   from synaplex.cognition import Mind
# etc.

__all__ = ["core", "cognition", "manifolds_indexers", "meta", "worlds"]
