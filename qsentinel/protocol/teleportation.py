"""Quantum teleportation with Pauli correction.

The prototype distributes every signature qubit by teleporting it through a
fresh Bell pair, which is what makes the scheme *teleportation-based* in the
sense required by the problem statement.  The three-qubit circuit is simulated
with an exact state vector:

1. ``CNOT(input -> sender_half)``
2. ``H(input)``
3. measure ``input`` and ``sender_half`` in the computational basis
4. the receiver applies ``Z**m1 @ X**m2`` to its own half

Step 4 consumes the two classical bits ``(m1, m2)`` that travel over the
*classical* control channel.  An adversary who tampers with those bits makes
the receiver apply the wrong correction, leaving a residual Pauli error on the
received qubit - precisely the mechanism exploited by the
channel-manipulation attack in :mod:`qsentinel.attacks.channel_manipulation`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..quantum.gates import H, PAULI
from ..quantum.measurement import PauliOutcome
from ..quantum.statevector import StateVector

_CORRECTION_TABLE: dict[tuple[int, int], str] = {
    (0, 0): "I",
    (0, 1): "X",
    (1, 0): "Z",
    (1, 1): "Y",
}
_ALL_MESSAGES: tuple[tuple[int, int], ...] = ((0, 0), (0, 1), (1, 0), (1, 1))


@dataclass(frozen=True)
class TeleportationRecord:
    """Everything needed to audit one teleportation event."""

    outcome_input: PauliOutcome
    outcome_sender: PauliOutcome
    true_message: tuple[int, int]
    used_message: tuple[int, int]
    applied_correction: str
    residual_error: str

    @property
    def was_faithful(self) -> bool:
        """True when the correction matched the true Bell-measurement outcome."""
        return self.residual_error == "I"

    @property
    def message_was_tampered(self) -> bool:
        """True when the classical bits delivered to the receiver were altered."""
        return self.true_message != self.used_message

    def as_dict(self) -> dict[str, object]:
        """JSON-friendly view of the record."""
        return {
            "true_message": list(self.true_message),
            "used_message": list(self.used_message),
            "correction": self.applied_correction,
            "residual_error": self.residual_error,
            "faithful": self.was_faithful,
        }


def correction_pauli(m1: int, m2: int) -> str:
    """Return the Pauli label of the receiver's correction ``Z**m1 @ X**m2``.

    ``Z**0 X**0 = I``, ``Z**0 X**1 = X``, ``Z**1 X**0 = Z`` and
    ``Z**1 X**1 = -iY``; the global phase is irrelevant so ``ZX`` is reported
    as ``Y``.
    """
    key = (m1, m2)
    if key not in _CORRECTION_TABLE:
        raise ValueError("classical teleportation bits must be 0 or 1")
    return _CORRECTION_TABLE[key]


def correction_operator(m1: int, m2: int) -> np.ndarray:
    """Return the 2x2 matrix of the receiver's correction ``Z**m1 @ X**m2``."""
    key = (m1, m2)
    if key not in _CORRECTION_TABLE:
        raise ValueError("classical teleportation bits must be 0 or 1")
    operator = np.eye(2, dtype=complex)
    if m2 == 1:
        operator = PAULI["X"] @ operator
    if m1 == 1:
        operator = PAULI["Z"] @ operator
    return operator


def residual_pauli(
    true_m1: int, true_m2: int, used_m1: int, used_m2: int
) -> str:
    """Return the Pauli error left on the receiver when the classical message is wrong.

    The receiver applies ``Z**used_m1 X**used_m2`` rather than the true
    ``Z**true_m1 X**true_m2``; the paired Xs and Zs cancel, leaving one Pauli.
    """
    if (true_m1, true_m2) == (used_m1, used_m2):
        return "I"
    return correction_pauli(true_m1 ^ used_m1, true_m2 ^ used_m2)


def _tensor(payload: StateVector, bell: StateVector) -> StateVector:
    a = payload.amplitudes
    b = bell.amplitudes
    coeffs = [complex(x) * complex(y) for x in a for y in b]
    return StateVector(coeffs, 3)


def teleport(
    payload: StateVector,
    bell: StateVector,
    rng: np.random.Generator,
    tamper: bool = False,
    used_message: tuple[int, int] | None = None,
) -> tuple[StateVector, TeleportationRecord]:
    """Teleport ``payload`` through ``bell`` and return the receiver's qubit.

    ``payload`` acts on circuit qubit ``0``; ``bell`` provides circuit qubits
    ``1`` (kept by the sender) and ``2`` (the receiver's half).

    ``tamper=True`` simulates a compromised classical control channel: the
    receiver is handed one of the three classical messages that differ from
    the true one, so it applies the wrong Pauli correction.  ``used_message``
    overrides the delivered bits outright and is used by the tests.
    """
    if payload.num_qubits != 1:
        raise ValueError("payload must be a single-qubit state")
    if bell.num_qubits != 2:
        raise ValueError("Bell resource must be a two-qubit state")

    circuit = _tensor(payload, bell).apply_controlled_not(control=0, target=1)
    circuit = circuit.apply_one_qubit(H, 0)

    bits, collapsed = circuit.measure_qubits((0, 1), rng)
    m1, m2 = bits
    true_message = (m1, m2)
    prob_branch = float(
        circuit.probabilities()[int(f"{m1}{m2}0", 2)]
        + circuit.probabilities()[int(f"{m1}{m2}1", 2)]
    )

    if used_message is not None:
        delivered = tuple(used_message)
        if len(delivered) != 2 or any(bit not in (0, 1) for bit in delivered):
            raise ValueError("used_message must be a pair of 0/1 bits")
    elif tamper:
        alternatives = [msg for msg in _ALL_MESSAGES if msg != true_message]
        delivered = alternatives[int(rng.integers(0, len(alternatives)))]
    else:
        delivered = true_message

    receiver_state = collapsed.reduced_single_qubit(2)
    corrected = receiver_state.apply_one_qubit(correction_operator(*delivered), 0)

    record = TeleportationRecord(
        outcome_input=PauliOutcome("Z", 1 - 2 * m1, prob_branch),
        outcome_sender=PauliOutcome("Z", 1 - 2 * m2, prob_branch),
        true_message=true_message,
        used_message=delivered,
        applied_correction=correction_pauli(*delivered),
        residual_error=residual_pauli(*true_message, *delivered),
    )
    return corrected, record
