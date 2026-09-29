"""Two independent, non-learning detection layers over the same measurement data."""

from .base import (
    DetectionInput,
    DetectionResult,
    Detector,
    PauliSignal,
    StatisticalSignal,
)
from .engine import PAULI, STATISTICAL, DetectionEngine, DetectionReport, build_input
from .pauli import PauliMeasurementDetector, measurement_summary
from .statistical import StatisticalDetector

__all__ = [
    "PAULI",
    "STATISTICAL",
    "DetectionEngine",
    "DetectionInput",
    "DetectionReport",
    "DetectionResult",
    "Detector",
    "PauliMeasurementDetector",
    "PauliSignal",
    "StatisticalDetector",
    "StatisticalSignal",
    "build_input",
    "measurement_summary",
]
