"""Verification: single-qubit checks, distillable amplification, and the witness.

The verifier holds the message and the shared key, so it knows the intended
basis ``sigma_i`` and eigenvalue ``(-1)**v_i`` at every position, and can
therefore classify every measurement as correct or incorrect.  It runs three
independent families of checks, all of which consume exact projective
measurement statistics:

``single``
    measure ``sigma`` on every one of the ``L * n`` received copies.  With
    group size ``g = 1`` this is the whole protocol: it detects an error on a
    given copy with probability ``1 - q`` where ``q`` is the per-copy error
    rate.
``parity``
    the *distillable amplification* check.  For each group of ``g`` copies
    drawn from the same message position, measure the cat-state observable
    ``sigma (x) ... (x) sigma``.  Because the group factorises, a group holding
    an *odd* number of errors always flips the parity, so a single error is
    detected with probability 1 instead of ``1 - q``.
``witness``
    two-body Pauli correlators of the retained Bell pairs, compared against
    the ideal resource.
"""

from __future__ import annotations

import numpy as np

from ..config import ProtocolConfig
from ..quantum.measurement import (
    ParityOutcome,
    correlator,
    measure_pauli,
    parity_measurement,
    pauli_expectation,
)
from .state import (
    CheckResult,
    DistributedState,
    VerificationReport,
)

WITNESS_CORRELATORS: tuple[tuple[str, str], ...] = (("Z", "Z"), ("X", "X"), ("Z", "X"), ("X", "Z"))


def _expected_correlators(sign_lambda: int, basis: str) -> dict[tuple[str, str], int]:
    """Ideal two-body correlators of the Bell resource prepared in ``basis``.

    For ``|Phi(lambda)>_sigma = (|0,0>_sigma + lambda |1,1>_sigma) / sqrt(2)``:
    the correlator along the resource's own axis is always ``+1``, the
    correlator along the other axis carries the sign ``lambda``, and both
    crossed correlators vanish.  So a ``|Phi+>`` resource in the ``Z`` basis
    reads ``ZZ = +1, XX = +1`` while ``|Phi->`` in the ``X`` basis reads
    ``XX = +1, ZZ = -1`` - which is exactly why the basis must be recorded.
    """
    if basis not in ("X", "Z"):
        raise ValueError(f"unsupported witness basis {basis!r}")
    own = (basis, basis)
    other = ("X", "X") if basis == "Z" else ("Z", "Z")
    return {own: 1, other: sign_lambda, ("Z", "X"): 0, ("X", "Z"): 0}


def single_qubit_checks(
    distributed: DistributedState, rng: np.random.Generator
) -> tuple[tuple[CheckResult, ...], tuple]:
    """Measure ``sigma`` on every received copy and compare with the target."""
    results: list[CheckResult] = []
    outcomes = []
    for qubit in distributed.test_qubits:
        outcome = measure_pauli(qubit.state, 0, qubit.basis, rng)
        outcomes.append(outcome)
        passed = outcome.eigenvalue == qubit.expected_eigenvalue
        results.append(
            CheckResult(
                kind="single",
                label=f"pos{qubit.position}.copy{qubit.copy_index}",
                expected=qubit.expected_eigenvalue,
                observed=outcome.eigenvalue,
                passed=passed,
                detail=f"{qubit.basis}-basis eigenvalue",
            )
        )
    return tuple(results), tuple(outcomes)


def parity_groups(distribution_size: int, group_size: int) -> tuple[tuple[int, ...], ...]:
    """Split ``distribution_size`` copies into consecutive groups of ``group_size``."""
    if group_size < 1:
        raise ValueError("group_size must be positive")
    usable = (distribution_size // group_size) * group_size
    return tuple(
        tuple(range(start, start + group_size))
        for start in range(0, usable, group_size)
    )


def amplification_checks(
    distributed: DistributedState,
    group_size: int,
    rng: np.random.Generator,
) -> tuple[tuple[CheckResult, ...], tuple[ParityOutcome, ...]]:
    """Run the distillable-amplification parity check on every position."""
    results: list[CheckResult] = []
    outcomes: list[ParityOutcome] = []
    for position in range(distributed.transaction.length):
        copies = distributed.qubits_at(position)
        if not copies:
            continue
        basis = copies[0].basis
        for index, group in enumerate(parity_groups(len(copies), group_size)):
            members = [copies[member] for member in group]
            states = [member.state for member in members]
            expected_parity = 1
            for member in members:
                expected_parity *= member.expected_eigenvalue
            outcome = parity_measurement(states, basis, rng, expected=expected_parity)
            outcomes.append(outcome)
            results.append(
                CheckResult(
                    kind="parity",
                    label=f"pos{position}.group{index}",
                    expected=expected_parity,
                    observed=outcome.eigenvalue,
                    passed=outcome.eigenvalue == expected_parity,
                    detail=f"({basis} x {len(group)}) cat-state parity",
                )
            )
    return tuple(results), tuple(outcomes)


def coverage_checks(
    distributed: DistributedState, expected_copies: int
) -> tuple[CheckResult, ...]:
    """Check that every message position returned all of its teleportation copies.

    Qubit loss is invisible to a per-qubit measurement - a missing qubit simply
    is not measured - so the protocol has to count.  A shortfall means qubits
    were dropped, which is the observable signature of an intercept-and-resend
    adversary.
    """
    results: list[CheckResult] = []
    for position in range(distributed.transaction.length):
        observed = len(distributed.qubits_at(position))
        results.append(
            CheckResult(
                kind="coverage",
                label=f"pos{position}.coverage",
                expected=expected_copies,
                observed=observed,
                passed=observed == expected_copies,
                detail="teleportation copies returned",
            )
        )
    return tuple(results)


def witness_checks(
    distributed: DistributedState, tolerance: float = 1e-6
) -> tuple[tuple[CheckResult, ...], dict[tuple[str, str], float]]:
    """Compare the retained Bell pairs against the ideal correlator pattern."""
    results: list[CheckResult] = []
    aggregate: dict[tuple[str, str], float] = {}
    for pair in distributed.witness_pairs:
        expected = _expected_correlators(pair.expected_eigenvalue, pair.basis)
        passed = True
        for name in WITNESS_CORRELATORS:
            observed = correlator(pair.state, *name)
            aggregate[name] = aggregate.get(name, 0.0) + observed
            if abs(observed - expected[name]) > tolerance:
                passed = False
        results.append(
            CheckResult(
                kind="witness",
                label=f"witness{pair.index}",
                expected=pair.expected_eigenvalue,
                observed=int(pair.disturbed),
                passed=passed,
                detail=f"{pair.basis}-basis Bell correlators",
            )
        )
    count = max(len(distributed.witness_pairs), 1)
    return tuple(results), {name: value / count for name, value in aggregate.items()}


def expectation_statistics(distribution: DistributedState) -> dict[str, dict[str, float]]:
    """Per-basis mean Pauli expectation values, split by intended eigenvalue."""
    stats: dict[str, dict[str, float]] = {}
    for basis in ("X", "Z"):
        entries = [q for q in distribution.test_qubits if q.basis == basis]
        if not entries:
            continue
        stats[basis] = {}
        for eigenvalue in (1, -1):
            subset = [q for q in entries if q.expected_eigenvalue == eigenvalue]
            if not subset:
                continue
            values = [pauli_expectation(q.state, 0, basis) for q in subset]
            stats[basis][f"mean_{eigenvalue:+d}"] = float(np.mean(values))
            stats[basis][f"count_{eigenvalue:+d}"] = float(len(subset))
    return stats


def verify(
    distributed: DistributedState,
    protocol: ProtocolConfig,
    rng: np.random.Generator,
    freshness_ok: bool = True,
) -> VerificationReport:
    """Run every verification family and assemble the report.

    Parameters
    ----------
    distributed:
        What the receiver actually holds.
    protocol:
        Structural settings; supplies the distillation group size and the
        expected number of copies per position.
    freshness_ok:
        Result of the replay check, supplied by the caller because freshness is
        a classical protocol property rather than a quantum measurement.
    """
    group_size = protocol.parity_group_size
    single, single_outcomes = single_qubit_checks(distributed, rng)
    parity, parity_outcomes = amplification_checks(distributed, group_size, rng)
    witness, _ = witness_checks(distributed)
    coverage = coverage_checks(distributed, protocol.copies_per_bit)

    families = (*single, *parity, *witness, *coverage)
    signature_valid = all(check.passed for check in families)
    reasons = []
    if not all(check.passed for check in witness):
        reasons.append("entanglement witness mismatch")
    if not all(check.passed for check in single):
        reasons.append("per-copy measurement mismatch")
    if not all(check.passed for check in parity):
        reasons.append("distillation parity mismatch")
    if not all(check.passed for check in coverage):
        reasons.append("missing teleportation copies")
    if not freshness_ok:
        reasons.append("nonce replay")
    if not distributed.transaction.authorised:
        reasons.append("unauthorised verifying entity")

    return VerificationReport(
        transaction=distributed.transaction,
        distributed=distributed,
        single_checks=single,
        parity_checks=parity,
        witness_checks=witness + coverage,
        parity_outcomes=parity_outcomes,
        single_outcomes=single_outcomes,
        signature_valid=signature_valid,
        freshness_ok=freshness_ok,
        authorisation_ok=distributed.transaction.authorised,
        reject_reason="; ".join(reasons),
    )
