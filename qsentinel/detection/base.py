"""Detector interface shared by both detection layers.

Both layers consume the *same* :class:`DetectionInput` so that the comparison
between them is fair: identical scenarios, identical measurement data,
different decision rules.  No AI, no machine learning, no fitted parameters -
each layer is a fixed set of arithmetic rules over measured quantities.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..config import DetectionConfig
from ..protocol.state import DistributedState, VerificationReport


@dataclass(frozen=True)
class StatisticalSignal:
    """One threshold comparison performed by the statistical layer."""

    name: str
    value: float
    threshold: float
    comparison: str
    tripped: bool
    description: str

    def as_dict(self) -> dict[str, Any]:
        """JSON-friendly view of the signal."""
        return {
            "name": self.name,
            "value": self.value,
            "threshold": self.threshold,
            "comparison": self.comparison,
            "tripped": self.tripped,
            "description": self.description,
        }


@dataclass(frozen=True)
class PauliSignal:
    """One expectation-value comparison performed by the Pauli layer."""

    name: str
    value: float
    threshold: float
    comparison: str
    tripped: bool
    description: str

    def as_dict(self) -> dict[str, Any]:
        """JSON-friendly view of the signal."""
        return {
            "name": self.name,
            "value": self.value,
            "threshold": self.threshold,
            "comparison": self.comparison,
            "tripped": self.tripped,
            "description": self.description,
        }


@dataclass(frozen=True)
class DetectionInput:
    """Everything a detector is allowed to look at."""

    report: VerificationReport
    detection_config: DetectionConfig
    authorised_entities: frozenset[str] = frozenset()
    context_notes: dict[str, Any] = field(default_factory=dict)

    @property
    def distributed(self) -> DistributedState:
        """The received quantum state the decision is based on."""
        return self.report.distributed


@dataclass(frozen=True)
class DetectionResult:
    """The verdict of one detector on one transaction."""

    detector: str
    is_threat: bool
    signals: tuple[Any, ...]
    summary: str

    @property
    def tripped_signals(self) -> tuple[str, ...]:
        """Names of the signals that fired."""
        return tuple(signal.name for signal in self.signals if signal.tripped)

    def as_dict(self) -> dict[str, Any]:
        """JSON-friendly view of the verdict."""
        return {
            "detector": self.detector,
            "is_threat": self.is_threat,
            "tripped_signals": list(self.tripped_signals),
            "summary": self.summary,
            "signals": [signal.as_dict() for signal in self.signals],
        }


class Detector(ABC):
    """Base class for a threshold-based, non-learning detector."""

    name: str = ""
    description: str = ""
    consumes: str = ""

    @abstractmethod
    def analyse(self, data: DetectionInput) -> DetectionResult:
        """Return the detector's verdict for one transaction."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name!r})"
