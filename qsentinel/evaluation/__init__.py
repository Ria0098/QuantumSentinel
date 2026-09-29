"""Controlled experiments, confusion-matrix metrics and parameter sweeps."""

from .metrics import ConfusionMatrix, confusion_from_labels, mean, wilson_interval
from .runner import (
    EvaluationResult,
    TrialRecord,
    run_evaluation,
    run_group_size_sweep,
    run_noise_sweep,
)

__all__ = [
    "ConfusionMatrix",
    "EvaluationResult",
    "TrialRecord",
    "confusion_from_labels",
    "mean",
    "run_evaluation",
    "run_group_size_sweep",
    "run_noise_sweep",
    "wilson_interval",
]
