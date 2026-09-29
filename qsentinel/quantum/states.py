"""Pauli eigenstates and basis-dependent Bell pairs.

The qubit-wise QDS protocol in :mod:`qsentinel.protocol` only ever uses states
that are eigenstates of a single Pauli observable, and only ever measures in
that same basis.  Writing ``|b>_sigma`` for the ``sigma`` eigenstate with
eigenvalue ``(-1)**b``:

* the signature qubit for message bit ``b`` in basis ``sigma`` is ``|b>_sigma``;
* the distribution resource in basis ``sigma`` is the Bell state

  ``|Phi(lambda)>_sigma = (|0,0>_sigma + lambda |1,1>_sigma) / sqrt(2)``

  which reduces to the familiar ``( |00> + lambda |11> ) / sqrt(2)`` in the
  computational basis and to its Hadamard-conjugate state in the X basis.

The shared secret key ``k`` selects the basis (``k_i = 0`` -> ``Z``,
``k_i = 1`` -> ``X``), so an adversary without the key cannot predict which
observable an honest signature qubit is an eigenstate of.
"""

from __future__ import annotations

import numpy as np

from .gates import PAULI, to_eigenbasis
from .statevector import StateVector

NON_TRIVIAL_PAULIS: tuple[str, ...] = ("X", "Y", "Z")


def pauli_eigenstate(bit: int, basis: str) -> StateVector:
    """Return ``|bit>_basis``, the eigenstate of ``basis`` with eigenvalue ``(-1)**bit``."""
    if bit not in (0, 1):
        raise ValueError("bit must be 0 or 1")
    if basis not in ("X", "Y", "Z"):
        raise ValueError(f"unsupported basis {basis!r}")
    return StateVector.from_label(str(bit)).apply_one_qubit(to_eigenbasis(basis), 0)


def basis_for_key_bit(key_bit: int) -> str:
    """Map a secret-key bit to the measurement basis it dictates."""
    if key_bit not in (0, 1):
        raise ValueError("key bit must be 0 or 1")
    return "Z" if key_bit == 0 else "X"


def bell_pair(eigenvalue: int, basis: str) -> StateVector:
    """Return ``|Phi(eigenvalue)>_basis``, the maximally entangled distribution resource.

    The receiver's second qubit is a ``basis`` eigenstate, so a Bell measurement
    on the sender's halves transfers the signature eigenvalue to the receiver.
    """
    if eigenvalue not in (-1, 1):
        raise ValueError("Bell eigenvalue must be +1 or -1")
    if basis not in ("X", "Y", "Z"):
        raise ValueError(f"unsupported basis {basis!r}")
    state = StateVector.from_superposition(["00", "11"], [1.0, float(eigenvalue)])
    if basis != "Z":
        rotation = to_eigenbasis(basis)
        state = state.apply_one_qubit(rotation, 0).apply_one_qubit(rotation, 1)
    return state


def apply_pauli(state: StateVector, qubit: int, pauli: str) -> StateVector:
    """Return a new state with Pauli operator ``pauli`` applied to ``qubit``."""
    return state.apply_one_qubit(PAULI[pauli], qubit)


def pauli_error(rng: np.random.Generator, weight: float = 1.0) -> str:
    """Draw a Pauli error, with identity probability ``1 - weight``."""
    if not 0.0 <= weight <= 1.0:
        raise ValueError("error weight must lie in [0, 1]")
    if weight <= 0.0:
        return "I"
    draw = float(rng.random())
    if weight >= 1.0:
        return NON_TRIVIAL_PAULIS[int(rng.integers(0, 3))]
    if draw < weight:
        return NON_TRIVIAL_PAULIS[int(rng.integers(0, 3))]
    return "I"


def sample_non_identity_pauli(rng: np.random.Generator) -> str:
    """Draw a uniformly random non-identity Pauli error."""
    return NON_TRIVIAL_PAULIS[int(rng.integers(0, 3))]
