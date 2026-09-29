"""Projective (Pauli / GHZ-parity) measurement statistics.

Every measurement performed anywhere in the prototype funnels through this
module, so that the two detection layers consume exactly the same data:

* :func:`measure_pauli` - projective measurement of one qubit in a Pauli basis.
* :func:`parity_measurement` - projective measurement of the ``j``-qubit
  product (cat-state) observable ``sigma (x) sigma (x) ... (x) sigma`` over a
  group of ``j`` qubits.  This is the *distillable amplification* check: a
  single error anywhere inside the group flips the parity deterministically,
  so the probability of detecting at least one error inside the group rises
  from ``1 - (1 - p)**j`` (independent checks) to ``1 - (1 - p)`` (one check).
* :func:`correlator` - exact two-body Pauli correlator used for the
  entanglement-witness (CHSH) statistic.

All probabilities are obtained from the Born rule on exact state vectors; no
sampling-based estimator or learned model is involved.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .gates import PAULI
from .statevector import StateVector

BASES: tuple[str, ...] = ("X", "Y", "Z")


@dataclass(frozen=True)
class PauliOutcome:
    """One projective Pauli measurement result."""

    pauli: str
    eigenvalue: int
    probability: float

    def __post_init__(self) -> None:
        if self.pauli not in BASES:
            raise ValueError(f"unsupported measurement observable {self.pauli!r}")
        if self.eigenvalue not in (-1, 1):
            raise ValueError("Pauli eigenvalue must be +1 or -1")

    @property
    def bit(self) -> int:
        """Computational label of the outcome (``0`` for +1, ``1`` for -1)."""
        return 0 if self.eigenvalue == 1 else 1


def pauli_expectation(state: StateVector, qubit: int, pauli: str) -> float:
    """Exact single-qubit expectation value ``<state|sigma_q|state>``."""
    marginal = state.reduced_single_qubit(qubit)
    return float(np.real(marginal.expectation(PAULI[pauli])))


def measure_pauli(
    state: StateVector,
    qubit: int,
    pauli: str,
    rng: np.random.Generator | None = None,
) -> PauliOutcome:
    """Perform a projective measurement of ``sigma_q`` on ``qubit``.

    The outcome is sampled from the Born distribution
    ``P(+1) = (1 + <sigma_q>) / 2``.  For an eigenstate the expectation is
    ``+/-1`` and the outcome is deterministic, which is what makes the
    legitimate baseline reproducible without any noise model.
    """
    expected = pauli_expectation(state, qubit, pauli)
    prob_plus = min(1.0, max(0.0, 0.5 * (1.0 + expected)))
    if rng is None or prob_plus in (0.0, 1.0):
        eigenvalue = 1 if prob_plus >= 0.5 else -1
    else:
        eigenvalue = 1 if rng.random() < prob_plus else -1
    return PauliOutcome(pauli=pauli, eigenvalue=eigenvalue, probability=prob_plus)


@dataclass(frozen=True)
class ParityOutcome:
    """Result of a multi-qubit product-observable (cat-state) measurement."""

    group_size: int
    eigenvalue: int
    probability: float
    eigenvalues: tuple[int, ...]
    expectations: tuple[float, ...]
    pauli: str = "Z"
    expected: int = 1

    @property
    def is_deterministic(self) -> bool:
        """True when every member of the group was a Pauli eigenstate."""
        return all(abs(value) > 1.0 - 1e-9 for value in self.expectations)

    @property
    def expectation(self) -> float:
        """The measured ``<Pi>`` for the cat-state observable."""
        product = 1.0
        for value in self.expectations:
            product *= value
        return float(np.clip(product, -1.0, 1.0))

    @property
    def agrees_with_expected(self) -> bool:
        """True when the observed parity matched the intended parity."""
        return self.eigenvalue == self.expected


def parity_expectation(states: Sequence[StateVector], pauli: str) -> float:
    """Exact expectation of ``sigma (x) ... (x) sigma`` for a product state."""
    if not states:
        raise ValueError("parity group must be non-empty")
    value = 1.0
    for state in states:
        value *= pauli_expectation(state, 0, pauli)
    return float(np.clip(value, -1.0, 1.0))


def parity_measurement(
    states: Sequence[StateVector],
    pauli: str,
    rng: np.random.Generator | None = None,
    expected: int = 1,
) -> ParityOutcome:
    """Measure the cat-state parity observable over a group of single-qubit states.

    The observable is ``Pi = sigma (x) sigma (x) ... (x) sigma``.  Because the
    qubits form a product state, ``<Pi> = prod_j <sigma_j>`` and the Born rule
    gives ``P(parity = +1) = (1 + <Pi>) / 2``.  Note this is *not* the
    probability that every qubit reads ``+1``: an even number of ``-1`` outcomes
    also yields parity ``+1``, which is exactly why the check detects an odd
    number of errors with probability 1.

    ``expected`` records the intended parity the detector considers correct for
    this group (the product of the group's target eigenvalues), so the
    measurement can be judged without needing the group membership again.
    """
    expectations = tuple(pauli_expectation(state, 0, pauli) for state in states)
    parity_value = 1.0
    for value in expectations:
        parity_value *= value
    parity_value = float(np.clip(parity_value, -1.0, 1.0))
    prob_plus = min(1.0, max(0.0, 0.5 * (1.0 + parity_value)))
    eigenvalues = tuple(1 if value >= 0.0 else -1 for value in expectations)
    if rng is None or prob_plus in (0.0, 1.0):
        parity = 1 if prob_plus >= 0.5 else -1
    else:
        parity = 1 if rng.random() < prob_plus else -1
    return ParityOutcome(
        group_size=len(states),
        eigenvalue=parity,
        probability=prob_plus,
        eigenvalues=eigenvalues,
        expectations=expectations,
        pauli=pauli,
        expected=expected,
    )


def correlator(state: StateVector, pauli_a: str, pauli_b: str) -> float:
    """Exact correlator ``<sigma_a (x) sigma_b>`` for a two-qubit state."""
    if state.num_qubits != 2:
        raise ValueError("correlator is defined for two-qubit states")
    observable = np.kron(PAULI[pauli_a], PAULI[pauli_b])
    return float(np.real(state.expectation(observable)))


def chsh_value(
    e_zz: float, e_zx: float, e_xz: float, e_xx: float
) -> float:
    """CHSH combination ``|E_zz + E_zx + E_xz - E_xx|``."""
    return float(abs(e_zz + e_zx + e_xz - e_xx))
