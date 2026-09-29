"""Method 2 - Pauli-measurement-based detection.

This layer is deliberately restricted to *quantum measurement data*.  It never
looks at nonces, sender identities or authorisation state, which is what makes
the two-layer comparison in the report informative: where the two layers
disagree, the disagreement is a statement about what quantum measurements can
and cannot establish.

Signals
-------
``eigenvalue_agreement_<basis>``
    for each key-dictated basis, the mean Pauli expectation value of the
    received copies that were *supposed* to be the ``+1`` eigenstate.  A
    correct run gives exactly ``+1``; any disturbance pulls it toward ``0``.
``basis_distribution_distance_<basis>``
    total-variation distance between the observed and the *expected* fraction
    of ``+1`` outcomes in that basis.  The expectation is computed from the
    verifier's own record of the message, not assumed to be uniform, because
    the aggregate over many copies is message-dependent even though each
    individual copy leaks nothing.
``parity_agreement_<basis>``
    fraction of distillation groups in ``basis`` whose measured cat-state
    parity matched the group's intended parity.  This is the amplified
    statistic: an odd number of errors inside a group flips the parity with
    probability 1, whereas the per-copy signal only degrades by
    ``1 / group_size``.
``entanglement_witness``
    fraction of retained Bell pairs whose two-body Pauli correlator pattern
    still matches the ideal resource - the only signal that speaks about the
    channel rather than about the signature.

By construction this layer **cannot** see replay or unauthorised
verification: both leave the Pauli measurement data bit-identical to a
legitimate run.  The evaluation reports that as a measured false negative
rather than a convenient 100% detection rate.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ..quantum.measurement import pauli_expectation
from ..protocol.verifier import witness_checks
from .base import DetectionInput, DetectionResult, Detector, PauliSignal

BASES: tuple[str, ...] = ("X", "Z")


def mean_expectation(data: DetectionInput, basis: str) -> float:
    """Mean Pauli expectation value over every received copy in ``basis``.

    On a correct run this equals ``2 * observed_positive_fraction - 1`` and
    is *not* zero: the aggregate depends on the message and key, both of which
    the verifier knows.  It is reported for inspection and is deliberately not
    used as a trip condition - the distance to the *expected* fraction is.
    """
    copies = data.distributed.in_basis(basis)
    if not copies:
        return 0.0
    return float(np.mean([pauli_expectation(c.state, 0, basis) for c in copies]))


def expected_positive_fraction(data: DetectionInput, basis: str) -> float:
    """Fraction of copies in ``basis`` that should read ``+1`` for this message.

    Computed from the verifier's own record of the transaction, so it is a
    property of the signed message rather than of the observation.
    """
    positions = [
        index
        for index in range(data.report.transaction.length)
        if data.report.transaction.basis_at(index) == basis
    ]
    if not positions:
        return 0.0
    positive = sum(
        1
        for index in positions
        if data.report.transaction.expected_eigenvalue_at(index) == 1
    )
    return positive / len(positions)


def observed_positive_fraction(data: DetectionInput, basis: str) -> float:
    """Fraction of received copies in ``basis`` that actually read ``+1``."""
    copies = data.distributed.in_basis(basis)
    if not copies:
        return 0.0
    positive = sum(
        1 for copy in copies if pauli_expectation(copy.state, 0, basis) > 0.0
    )
    return positive / len(copies)


def eigenvalue_agreement(data: DetectionInput, basis: str) -> float:
    """Mean Pauli expectation over copies intended to be the ``+1`` eigenstate."""
    positives = [c for c in data.distributed.in_basis(basis) if c.expected_eigenvalue == 1]
    if not positives:
        return 1.0
    return float(np.mean([pauli_expectation(c.state, 0, basis) for c in positives]))


def basis_distribution_distance(data: DetectionInput, basis: str) -> float:
    """Total-variation distance between observed and expected outcome histograms.

    Both the observed and the expected fraction of ``+1`` outcomes are
    two-point distributions, so their total-variation distance is simply the
    absolute difference of the two positive fractions.  A correct run gives
    exactly ``0``.
    """
    observed = observed_positive_fraction(data, basis)
    expected = expected_positive_fraction(data, basis)
    return float(min(1.0, abs(observed - expected)))


def parity_agreement(data: DetectionInput, basis: str) -> float:
    """Fraction of cat-state parities in ``basis`` matching their intended value."""
    outcomes = [o for o in data.report.parity_outcomes if o.pauli == basis]
    if not outcomes:
        return 1.0
    return float(np.mean([1.0 if o.agrees_with_expected else 0.0 for o in outcomes]))


def entanglement_agreement(data: DetectionInput) -> float:
    """Fraction of witness pairs whose two-body Pauli correlators still match."""
    checks, _ = witness_checks(data.distributed)
    if not checks:
        return 1.0
    return sum(1 for check in checks if check.passed) / len(checks)


def measurement_summary(data: DetectionInput) -> dict[str, Any]:
    """Collect every Pauli-measurement statistic the detector consumes."""
    return {
        basis: {
            "copies": len(data.distributed.in_basis(basis)),
            "expected_positive_fraction": expected_positive_fraction(data, basis),
            "observed_positive_fraction": observed_positive_fraction(data, basis),
            "mean_expectation": mean_expectation(data, basis),
            "eigenvalue_agreement": eigenvalue_agreement(data, basis),
            "distribution_distance": basis_distribution_distance(data, basis),
            "parity_agreement": parity_agreement(data, basis),
        }
        for basis in BASES
    }


class PauliMeasurementDetector(Detector):
    """Measurement-based detector comparing expected against observed Pauli data."""

    name = "pauli_measurement"
    description = (
        "Quantum-inspired detection from Pauli expectation values, per-basis "
        "outcome distributions, cat-state parities and entanglement correlators."
    )
    consumes = "Pauli measurement outcomes only (no protocol context)"

    def analyse(self, data: DetectionInput) -> DetectionResult:
        """Return the composite measurement-based verdict."""
        config = data.detection_config
        agreement_threshold = config.parity_expectation_threshold
        signals: list[PauliSignal] = []

        for basis in BASES:
            agreement = eigenvalue_agreement(data, basis)
            signals.append(
                PauliSignal(
                    name=f"eigenvalue_agreement_{basis}",
                    value=agreement,
                    threshold=agreement_threshold,
                    comparison="<",
                    tripped=agreement < agreement_threshold,
                    description=f"mean <{basis}> over copies targeting the +1 eigenstate",
                )
            )
            distance = basis_distribution_distance(data, basis)
            signals.append(
                PauliSignal(
                    name=f"basis_distribution_distance_{basis}",
                    value=distance,
                    threshold=config.distribution_distance_threshold,
                    comparison=">",
                    tripped=distance > config.distribution_distance_threshold,
                    description=(
                        f"total-variation distance between the observed {basis}-basis "
                        "outcome histogram and the expected uniform one"
                    ),
                )
            )
            parity = parity_agreement(data, basis)
            signals.append(
                PauliSignal(
                    name=f"parity_agreement_{basis}",
                    value=parity,
                    threshold=agreement_threshold,
                    comparison="<",
                    tripped=parity < agreement_threshold,
                    description=(
                        f"fraction of {basis}-basis cat-state groups whose parity "
                        "matched the intended value"
                    ),
                )
            )

        witness = entanglement_agreement(data)
        signals.append(
            PauliSignal(
                name="entanglement_witness",
                value=witness,
                threshold=config.correlator_agreement_threshold,
                comparison="<",
                tripped=witness < config.correlator_agreement_threshold,
                description=(
                    "fraction of retained Bell pairs whose two-body Pauli correlators "
                    "still match the ideal resource"
                ),
            )
        )

        tripped = [signal.name for signal in signals if signal.tripped]
        if tripped:
            summary = "THREAT: " + ", ".join(tripped)
        else:
            summary = (
                "LEGITIMATE: Pauli expectation values, outcome distributions, "
                "cat-state parities and correlators all matched expectations"
            )
        return DetectionResult(
            detector=self.name,
            is_threat=bool(tripped),
            signals=tuple(signals),
            summary=summary,
        )


