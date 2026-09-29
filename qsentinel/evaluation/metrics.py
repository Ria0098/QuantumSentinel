"""Confusion-matrix metrics and Wilson score intervals.

No statistical test here is fitted or learned: these are closed-form counts and
closed-form binomial confidence intervals, computed from the ground-truth
labels the controlled experiments already carry.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable

Z_95 = 1.959963984540054


@dataclass(frozen=True)
class ConfusionMatrix:
    """Binary confusion matrix for one detector on one scenario."""

    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0

    @property
    def total(self) -> int:
        return (
            self.true_positives
            + self.false_positives
            + self.true_negatives
            + self.false_negatives
        )

    @property
    def positives(self) -> int:
        return self.true_positives + self.false_negatives

    @property
    def negatives(self) -> int:
        self_check = self.true_negatives + self.false_positives
        return self_check

    @property
    def detection_rate(self) -> float:
        """``TP / (TP + FN)`` - recall over attack transactions."""
        return _ratio(self.true_positives, self.positives)

    @property
    def false_alarm_rate(self) -> float:
        """``FP / (FP + TN)`` over legitimate transactions."""
        return _ratio(self.false_positives, self.negatives)

    @property
    def accuracy(self) -> float:
        """``(TP + TN) / (TP + TN + FP + FN)``."""
        return _ratio(self.true_positives + self.true_negatives, self.total)

    def add(self, other: "ConfusionMatrix") -> "ConfusionMatrix":
        """Return the element-wise sum of two matrices."""
        return ConfusionMatrix(
            true_positives=self.true_positives + other.true_positives,
            false_positives=self.false_positives + other.false_positives,
            true_negatives=self.true_negatives + other.true_negatives,
            false_negatives=self.false_negatives + other.false_negatives,
        )

    def as_dict(self) -> dict[str, Any]:
        """JSON-friendly view including the derived rates and 95% intervals."""
        return {
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "true_negatives": self.true_negatives,
            "false_negatives": self.false_negatives,
            "total": self.total,
            "detection_rate": self.detection_rate,
            "false_alarm_rate": self.false_alarm_rate,
            "accuracy": self.accuracy,
            "detection_rate_ci95": wilson_interval(
                self.true_positives, self.positives
            ),
            "false_alarm_rate_ci95": wilson_interval(
                self.false_positives, self.negatives
            ),
        }


def _ratio(numerator: int, denominator: int) -> float:
    return 0.0 if denominator <= 0 else numerator / denominator


def wilson_interval(successes: int, trials: int, z: float = Z_95) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion.

    Preferred over the normal approximation here because several cells in the
    evaluation contain zero counts, where the Wald interval degenerates.
    """
    if trials <= 0:
        return (0.0, 0.0)
    proportion = successes / trials
    denominator = 1.0 + z * z / trials
    centre = proportion + z * z / (2.0 * trials)
    spread = z * math.sqrt(
        proportion * (1.0 - proportion) / trials + z * z / (4.0 * trials * trials)
    )
    lower = (centre - spread) / denominator
    upper = (centre + spread) / denominator
    return (max(0.0, lower), min(1.0, upper))


def confusion_from_labels(
    labels: Iterable[bool], predictions: Iterable[bool]
) -> ConfusionMatrix:
    """Build a confusion matrix from ground-truth labels and predictions."""
    tp = fp = tn = fn = 0
    for actual, predicted in zip(labels, predictions):
        if actual and predicted:
            tp += 1
        elif actual and not predicted:
            fn += 1
        elif not actual and predicted:
            fp += 1
        else:
            tn += 1
    return ConfusionMatrix(tp, fp, tn, fn)


def mean(values: Iterable[float]) -> float:
    """Arithmetic mean, or ``0.0`` for an empty iterable."""
    collected = list(values)
    return sum(collected) / len(collected) if collected else 0.0
