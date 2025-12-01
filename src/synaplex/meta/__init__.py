# synaplex/meta/__init__.py

"""
System-level evaluation and evolution.

Not imported by synaplex.worlds.*.
"""

from .evaluation import MetricsEngine
from .evolution import EvolutionEngine

__all__ = ["MetricsEngine", "EvolutionEngine"]
