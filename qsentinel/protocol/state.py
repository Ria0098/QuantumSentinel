"""Data structures describing one QDS transaction.

A transaction carries three different kinds of information, and keeping them
apart is what lets the two detection layers answer genuinely different
questions:

``QDSTransaction``
    the *ground truth* - message, shared key, transaction id, authorisation.
    Only the sender and the verifier know the key.
``SignatureBlock``
    the sender's prepared signature qubits, one per message position.
``DistributedState``
    what actually arrived at the receiver - test qubits that may have been
    disturbed, retained Bell witness pairs, and the classical teleportation
    transcript (including any tampering).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from ..quantum.measurement import PauliOutcome, ParityOutcome
from ..quantum.statevector import StateVector
from ..protocol.teleportation import TeleportationRecord


def derive_transaction_id(message: str, key: str, nonce: str) -> str:
    """Derive a stable transaction id from the message, key and nonce."""
    payload = json.dumps(
        {"message": message, "key": key, "nonce": nonce}, sort_keys=True
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class QDSTransaction:
    """Ground-truth description of a single signing transaction.

    The *signed value* at position ``i`` is ``v_i = m_i XOR k_i`` and the
    measurement basis is dictated by the key bit (``k_i = 0`` -> ``Z``,
    ``k_i = 1`` -> ``X``).  An adversary without the key can predict neither
    the basis nor the target eigenvalue, which is the property that makes the
    scheme a signature rather than plain data.
    """

    message: str
    key: str
    nonce: str
    sender_id: str
    verifier_id: str
    requesting_entity: str
    authorised: bool = True
    transaction_id: str = field(default="", compare=False)

    def __post_init__(self) -> None:
        if set(self.message) - {"0", "1"}:
            raise ValueError("message must be a binary string")
        if set(self.key) - {"0", "1"}:
            raise ValueError("key must be a binary string")
        if len(self.message) != len(self.key):
            raise ValueError("message and key must have equal length")
        if not self.sender_id or not self.verifier_id:
            raise ValueError("sender and verifier identifiers are required")
        if not self.requesting_entity:
            raise ValueError("requesting entity is required")
        if not self.transaction_id:
            object.__setattr__(
                self,
                "transaction_id",
                derive_transaction_id(self.message, self.key, self.nonce),
            )

    @property
    def length(self) -> int:
        """Number of message bits ``L``."""
        return len(self.message)

    @property
    def signed_values(self) -> tuple[int, ...]:
        """``v_i = m_i XOR k_i`` for every position."""
        return tuple(
            int(m) ^ int(k) for m, k in zip(self.message, self.key)
        )

    def basis_at(self, position: int) -> str:
        """Measurement basis dictated by the key bit at ``position``."""
        return "Z" if self.key[position] == "0" else "X"

    def expected_eigenvalue_at(self, position: int) -> int:
        """Target eigenvalue ``(-1)**v_position`` at ``position``."""
        return 1 - 2 * self.signed_values[position]

    def bases(self) -> tuple[str, ...]:
        """Per-position measurement bases."""
        return tuple(self.basis_at(i) for i in range(self.length))

    def expected_eigenvalues(self) -> tuple[int, ...]:
        """Per-position target eigenvalues."""
        return tuple(self.expected_eigenvalue_at(i) for i in range(self.length))

    def as_dict(self) -> dict[str, Any]:
        """JSON-friendly view (the key is redacted by the reporter)."""
        return {
            "transaction_id": self.transaction_id,
            "message": self.message,
            "nonce": self.nonce,
            "sender_id": self.sender_id,
            "verifier_id": self.verifier_id,
            "requesting_entity": self.requesting_entity,
            "authorised": self.authorised,
            "bases": list(self.bases()),
            "expected_eigenvalues": list(self.expected_eigenvalues()),
        }


@dataclass(frozen=True)
class SignatureBlock:
    """The sender's prepared signature qubits, one per message position."""

    transaction: QDSTransaction
    qubits: tuple[StateVector, ...]

    def __post_init__(self) -> None:
        if len(self.qubits) != self.transaction.length:
            raise ValueError("signature block must hold one qubit per position")

    @property
    def length(self) -> int:
        """Number of signature qubits."""
        return len(self.qubits)

    def as_dict(self) -> dict[str, Any]:
        """JSON-friendly view of the prepared signature."""
        return {
            "length": self.length,
            "qubits": [str(qubit) for qubit in self.qubits],
        }


@dataclass(frozen=True)
class TestQubit:
    """One teleportation copy of a signature qubit as it arrived at the receiver."""

    position: int
    copy_index: int
    basis: str
    expected_eigenvalue: int
    state: StateVector
    record: TeleportationRecord

    @property
    def is_errored(self) -> bool:
        """True when the received state is not the intended eigenstate."""
        from ..quantum.measurement import pauli_expectation

        observed = pauli_expectation(self.state, 0, self.basis)
        return abs(observed - self.expected_eigenvalue) > 1e-9

    def as_dict(self) -> dict[str, Any]:
        """JSON-friendly view of the received copy."""
        from ..quantum.measurement import pauli_expectation

        return {
            "position": self.position,
            "copy_index": self.copy_index,
            "basis": self.basis,
            "expected_eigenvalue": self.expected_eigenvalue,
            "residual_error": self.record.residual_error,
            "message_tampered": self.record.message_was_tampered,
            "expectation": round(pauli_expectation(self.state, 0, self.basis), 6),
            "errored": self.is_errored,
        }


@dataclass(frozen=True)
class WitnessPair:
    """A retained Bell pair used for the Pauli-measurement entanglement witness."""

    index: int
    basis: str
    expected_eigenvalue: int
    state: StateVector
    disturbed: bool = False

    def as_dict(self) -> dict[str, Any]:
        """JSON-friendly view including the two-body correlators."""
        from ..quantum.measurement import correlator

        return {
            "index": self.index,
            "basis": self.basis,
            "expected_eigenvalue": self.expected_eigenvalue,
            "disturbed": self.disturbed,
            "zz": round(correlator(self.state, "Z", "Z"), 6),
            "xx": round(correlator(self.state, "X", "X"), 6),
            "zx": round(correlator(self.state, "Z", "X"), 6),
            "xz": round(correlator(self.state, "X", "Z"), 6),
        }


@dataclass(frozen=True)
class DistributedState:
    """Everything the receiver holds after the (possibly disturbed) distribution."""

    transaction: QDSTransaction
    test_qubits: tuple[TestQubit, ...]
    witness_pairs: tuple[WitnessPair, ...]
    classical_transcript: tuple[tuple[int, int], ...]
    dropped_qubits: int = 0
    signature_substituted: bool = False

    def qubits_at(self, position: int) -> tuple[TestQubit, ...]:
        """All copies belonging to one message position."""
        return tuple(q for q in self.test_qubits if q.position == position)

    def states_at(self, position: int) -> tuple[StateVector, ...]:
        """Received states for one message position."""
        return tuple(q.state for q in self.qubits_at(position))

    def in_basis(self, basis: str) -> tuple[TestQubit, ...]:
        """All copies whose key bit selected ``basis``."""
        return tuple(q for q in self.test_qubits if q.basis == basis)

    def tampered_messages(self) -> int:
        """How many classical teleportation messages were altered."""
        return sum(1 for record in self.teleportation_records() if record.message_was_tampered)

    def teleportation_records(self) -> tuple[TeleportationRecord, ...]:
        """The per-copy classical transcript."""
        return tuple(q.record for q in self.test_qubits)

    def residual_errors(self) -> dict[str, int]:
        """Histogram of the residual Pauli errors left on the received copies."""
        histogram: dict[str, int] = {}
        for qubit in self.test_qubits:
            label = qubit.record.residual_error
            histogram[label] = histogram.get(label, 0) + 1
        return histogram

    def as_dict(self) -> dict[str, Any]:
        """JSON-friendly view of the whole distribution."""
        return {
            "test_qubit_count": len(self.test_qubits),
            "witness_pair_count": len(self.witness_pairs),
            "dropped_qubits": self.dropped_qubits,
            "signature_substituted": self.signature_substituted,
            "tampered_messages": self.tampered_messages(),
            "residual_errors": self.residual_errors(),
            "classical_transcript": [list(pair) for pair in self.classical_transcript],
        }


@dataclass(frozen=True)
class CheckResult:
    """Outcome of one verification check (single-qubit, parity or witness)."""

    kind: str
    label: str
    expected: int
    observed: int
    passed: bool
    detail: str = ""

    def as_dict(self) -> dict[str, Any]:
        """JSON-friendly view of the check."""
        return {
            "kind": self.kind,
            "label": self.label,
            "expected": self.expected,
            "observed": self.observed,
            "passed": self.passed,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class VerificationReport:
    """Complete output of the verifier for one transaction."""

    transaction: QDSTransaction
    distributed: DistributedState
    single_checks: tuple[CheckResult, ...]
    parity_checks: tuple[CheckResult, ...]
    witness_checks: tuple[CheckResult, ...]
    parity_outcomes: tuple[ParityOutcome, ...]
    single_outcomes: tuple[PauliOutcome, ...]
    signature_valid: bool
    freshness_ok: bool
    authorisation_ok: bool
    reject_reason: str = ""

    @property
    def accepted(self) -> bool:
        """True when the transaction passes every verification rule."""
        return (
            self.signature_valid
            and self.freshness_ok
            and self.authorisation_ok
        )

    def all_checks(self) -> tuple[CheckResult, ...]:
        """Every check performed, in reporting order."""
        return self.single_checks + self.parity_checks + self.witness_checks

    def mismatch_count(self) -> int:
        """Total number of failing checks across all three families."""
        return sum(1 for check in self.all_checks() if not check.passed)

    def mismatch_rate(self) -> int | float:
        """``E = N_mismatch / N`` over every check performed."""
        total = len(self.all_checks())
        if total == 0:
            return 0
        return self.mismatch_count() / total

    def as_dict(self) -> dict[str, Any]:
        """JSON-friendly view of the whole verification."""
        return {
            "transaction": self.transaction.as_dict(),
            "distributed": self.distributed.as_dict(),
            "signature_valid": self.signature_valid,
            "freshness_ok": self.freshness_ok,
            "authorisation_ok": self.authorisation_ok,
            "accepted": self.accepted,
            "reject_reason": self.reject_reason,
            "mismatch_count": self.mismatch_count(),
            "mismatch_rate": self.mismatch_rate(),
            "checks": [check.as_dict() for check in self.all_checks()],
        }
