"""Method 1 - classical statistical detection.

The statistical layer aggregates a fixed set of scalar statistics, compares each
against a constant threshold, and raises the alarm if **any** of them trips.
Nothing is learned, fitted or estimated from the attack data.

Signals
-------
``mismatch_rate``
    ``E = N_mismatch / N`` over every verification check (per-copy, parity,
    witness, coverage), thresholded at ``mismatch_threshold``.
``qber``
    per-copy quantum bit error rate - the mismatch rate restricted to the
    per-copy measurement family, which isolates the quantum data from the
    protocol bookkeeping.
``per_basis_qber_X`` / ``per_basis_qber_Z``
    the same rate computed separately for each key-dictated basis.  A
    single-basis excess indicates a basis-dependent disturbance.
``coverage_shortfall``
    fraction of message positions that returned fewer teleportation copies
    than the protocol distributes.  Catches intercept-and-resend, which a
    per-qubit measurement cannot see.
``replay``
    the classical freshness check: has this nonce been accepted before?
``authorisation``
    is the requesting entity allowed to run verification at all?

The last two are classical protocol rules rather than statistics, and they are
included deliberately: replay and unauthorised verification leave the Pauli
measurement data untouched, so a purely statistical rule set over measurements
could never catch them.  The evaluation reports this honestly.
"""

from __future__ import annotations

from ..protocol.state import VerificationReport
from .base import DetectionInput, DetectionResult, Detector, StatisticalSignal


def _rate(mismatches: int, total: int) -> float:
    return 0.0 if total <= 0 else mismatches / total


def mismatch_rate(report: VerificationReport) -> float:
    """``E = N_mismatch / N`` over every check performed."""
    total = len(report.all_checks())
    return _rate(report.mismatch_count(), total)


def qber(report: VerificationReport) -> float:
    """Per-copy quantum bit error rate over the single-qubit measurement family."""
    return _rate(
        sum(1 for check in report.single_checks if not check.passed),
        len(report.single_checks),
    )


def per_basis_qber(report: VerificationReport, basis: str) -> float:
    """QBER restricted to copies whose key bit selected ``basis``."""
    copies = report.distributed.in_basis(basis)
    if not copies:
        return 0.0
    failed = sum(1 for copy in copies if copy.is_errored)
    return _rate(failed, len(copies))


def coverage_shortfall(report: VerificationReport) -> float:
    """Fraction of message positions that returned too few copies."""
    checks = [c for c in report.all_checks() if c.kind == "coverage"]
    if not checks:
        return 0.0
    shortfall = sum(max(0, c.expected - c.observed) for c in checks)
    expected = sum(c.expected for c in checks)
    return _rate(shortfall, expected)


class StatisticalDetector(Detector):
    """Threshold-based detector over classical verification statistics."""

    name = "statistical"
    description = (
        "Classical statistics of the verification run compared against fixed "
        "thresholds, plus the freshness and authorisation rules."
    )
    consumes = "verification check outcomes and protocol context"

    def analyse(self, data: DetectionInput) -> DetectionResult:
        """Return the composite statistical verdict."""
        report = data.report
        config = data.detection_config

        signal_values = [
            StatisticalSignal(
                name="mismatch_rate",
                value=mismatch_rate(report),
                threshold=config.mismatch_threshold,
                comparison=">",
                tripped=mismatch_rate(report) > config.mismatch_threshold,
                description="fraction of all verification checks that failed",
            ),
            StatisticalSignal(
                name="qber",
                value=qber(report),
                threshold=config.qber_threshold,
                comparison=">",
                tripped=qber(report) > config.qber_threshold,
                description="per-copy quantum bit error rate",
            ),
            StatisticalSignal(
                name="per_basis_qber_X",
                value=per_basis_qber(report, "X"),
                threshold=config.per_basis_qber_threshold,
                comparison=">",
                tripped=per_basis_qber(report, "X") > config.per_basis_qber_threshold,
                description="QBER of copies measured in the X basis",
            ),
            StatisticalSignal(
                name="per_basis_qber_Z",
                value=per_basis_qber(report, "Z"),
                threshold=config.per_basis_qber_threshold,
                comparison=">",
                tripped=per_basis_qber(report, "Z") > config.per_basis_qber_threshold,
                description="QBER of copies measured in the Z basis",
            ),
            StatisticalSignal(
                name="coverage_shortfall",
                value=coverage_shortfall(report),
                threshold=0.0,
                comparison=">",
                tripped=coverage_shortfall(report) > 0.0,
                description="fraction of expected teleportation copies never returned",
            ),
            StatisticalSignal(
                name="replay",
                value=0.0 if report.freshness_ok else 1.0,
                threshold=0.0,
                comparison=">",
                tripped=not report.freshness_ok,
                description="nonce already accepted by the verifier",
            ),
            StatisticalSignal(
                name="authorisation",
                value=0.0 if report.authorisation_ok else 1.0,
                threshold=0.0,
                comparison=">",
                tripped=not report.authorisation_ok,
                description="requesting entity is not authorised to verify",
            ),
        ]

        tripped = [signal.name for signal in signal_values if signal.tripped]
        is_threat = bool(tripped)
        if is_threat:
            summary = "THREAT: " + ", ".join(tripped)
        else:
            summary = "LEGITIMATE: no statistical signal exceeded its threshold"
        return DetectionResult(
            detector=self.name,
            is_threat=is_threat,
            signals=tuple(signal_values),
            summary=summary,
        )
