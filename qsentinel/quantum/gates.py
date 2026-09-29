"""Single-qubit gates and Pauli operators in the computational basis."""

from __future__ import annotations

import numpy as np

I = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)
H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2.0)
S = np.array([[1, 0], [0, 1j]], dtype=complex)
SDG = S.conj().T
T = np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex)

PAULI: dict[str, np.ndarray] = {"I": I, "X": X, "Y": Y, "Z": Z}
PAULI_NAMES: tuple[str, ...] = ("I", "X", "Y", "Z")
_NON_TRIVIAL: tuple[str, ...] = ("X", "Y", "Z")


def rotation(pauli: str, angle: float) -> np.ndarray:
    """Return ``exp(-i * angle * sigma / 2)`` for ``sigma`` in ``{X, Y, Z}``."""
    if pauli not in _NON_TRIVIAL:
        raise ValueError(f"rotation requires X, Y or Z, got {pauli!r}")
    return np.cos(angle / 2.0) * I - 1j * np.sin(angle / 2.0) * PAULI[pauli]


def to_computational(basis: str) -> np.ndarray:
    """Return the unitary that maps a ``basis`` eigenstate onto a ``Z`` basis state.

    ``to_computational(sigma) @ |b>_sigma == |b>``, so a computational-basis
    measurement of the rotated state returns the label ``b``.  Used by the
    measurement layer.
    """
    if basis == "Z":
        return I
    if basis == "X":
        return H
    if basis == "Y":
        return H @ SDG
    raise ValueError(f"unknown measurement basis {basis!r}")


def to_eigenbasis(basis: str) -> np.ndarray:
    """Return the unitary that maps a ``Z`` basis state onto a ``basis`` eigenstate.

    ``to_eigenbasis(sigma) @ |b> == |b>_sigma``.  Used to build signature
    qubits, receiver states and Bell resources in the key-dictated basis.
    """
    return to_computational(basis).conj().T


def unitary_for_basis(basis: str) -> np.ndarray:
    """Alias for :func:`to_computational` (measurement-basis rotation)."""
    return to_computational(basis)


def anticommutes(pauli: str) -> str:
    """Return a non-identity Pauli that anticommutes with ``pauli``."""
    table = {
        "I": "X",
        "X": "Z",
        "Y": "Z",
        "Z": "X",
    }
    if pauli not in table:
        raise ValueError(f"unknown Pauli {pauli!r}")
    return table[pauli]
