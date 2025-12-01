# synaplex/meta/__init__.py

"""
System-level evaluation and evolution.

Not imported by synaplex.worlds.*.
"""

from .evaluation import MetricsEngine
from .evolution import EvolutionEngine
from .logging import RunLogger, RunMetadata, TickEvent
from .dna_utils import DNAUtils
from .manifold_utils import ManifoldUtils
from .experiments import NatureNurtureExperiment, NurtureNatureExperiment, PopulationExperiment
from .trajectories import ManifoldTrajectory, TrajectoryPoint, TrajectoryAnalyzer
from .population import Population, PopulationConfig, bootstrap_population
from .cultural_drift import CulturalDriftAnalyzer
from .experiment_state import (
    ExperimentState,
    ExperimentCheckpoint,
    IncrementalLogger,
    ExperimentRunner,
)

__all__ = [
    "MetricsEngine",
    "EvolutionEngine",
    "RunLogger",
    "RunMetadata",
    "TickEvent",
    "DNAUtils",
    "ManifoldUtils",
    "NatureNurtureExperiment",
    "NurtureNatureExperiment",
    "PopulationExperiment",
    "ManifoldTrajectory",
    "TrajectoryPoint",
    "TrajectoryAnalyzer",
    "Population",
    "PopulationConfig",
    "bootstrap_population",
    "CulturalDriftAnalyzer",
    "ExperimentState",
    "ExperimentCheckpoint",
    "IncrementalLogger",
    "ExperimentRunner",
]
