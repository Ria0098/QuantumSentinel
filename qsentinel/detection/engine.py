"""Detection engine: runs both layers and compares their verdicts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..config import DetectionConfig
from .base import DetectionInput, DetectionResult, Detector
from .pauli import PauliMeasurementDetector, measurement_summary
from .statistical import StatisticalDetector

STATISTICAL = "statistical"
PAULI = "pauli_measurement"


@dataclass(frozen=True)
class DetectionReport:
    """Both verdicts on one transaction, plus their agreement."""

    statistical: DetectionResult
    pauli: DetectionResult
    measurement_summary: dict[str, Any]

    @property
    def agree(self) -> bool:
        """True when both layers reached the same verdict."""
        return self.statistical.is_threat == self.pauli.is_threat

    @property
    def any_threat(self) -> bool:
        """True when at least one layer raised the alarm."""
        return self.statistical.is_threat or self.pauli.is_threat

    def measures(self) -> dict[str, Any]:
        """Flatten every signal from both layers into ``{name: signal}``."""
        combined: dict[str, Any] = {}
        for detector in (self.statistical, self.pauli):
            for signal in detector.signals:
                combined[signal.name] = signal
        return combined

    def verdicts(self) -> dict[str, bool]:
        """Map detector name to verdict."""
        return {
            self.statistical.detector: self.statistical.is_threat,
            self.pauli.detector: self.pauli.is_threat,
        }

    def as_dict(self) -> dict[str, Any]:
        """JSON-friendly view of both verdicts."""
        return {
            "agree": self.agree,
            "any_threat": self.any_threat,
            "verdicts": self.verdicts(),
            "statistical": self.statistical.as_dict(),
            "pauli_measurement": self.pauli.as_dict(),
            "measurement_summary": self.measurement_summary,
        }


class DetectionEngine:
    """Runs a collection of detectors over the same input."""

    def __init__(self, detectors: tuple[Detector, ...] | None = None) -> None:
        if detectors is None:
            detectors = (StatisticalDetector(), PauliMeasurementDetector())
        if not detectors:
            raise ValueError("at least one detector is required")
        self.detectors = detectors

    def run(self, data: DetectionInput) -> DetectionReport:
        """Run every detector and pair the statistical and Pauli verdicts."""
        results = {detector.name: detector.analyse(data) for detector in self.detectors}
        if STATISTICAL not in results or PAULI not in results:
            raise ValueError(
                "the engine requires both the statistical and Pauli-measurement detectors"
            )
        return DetectionReport(
            statistical=results[STATISTICAL],
            pauli=results[PAULI],
            measurement_summary=measurement_summary(data),
        )

    def __repr__(self) -> str:
        names = ", ".join(detector.name for detector in self.detectors)
        return f"DetectionEngine({names})"


def build_input(
    report,
    config: DetectionConfig,
    authorised_entities: frozenset[str],
    context_notes: dict[str, Any] | None = None,
) -> DetectionInput:
    """Convenience constructor for :class:`DetectionInput`."""
    return DetectionInput(
        report=report,
        detection_config=config,
        authorised_entities=authorised_entities,
        context_notes=dict(context_notes or {}),
    )
