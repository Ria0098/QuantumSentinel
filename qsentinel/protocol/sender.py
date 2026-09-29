"""Sender side of the QDS protocol: key handling and signature generation."""

from __future__ import annotations

import numpy as np

from ..quantum.states import pauli_eigenstate
from .state import QDSTransaction, SignatureBlock


def random_bits(rng: np.random.Generator, length: int) -> str:
    """Return a uniformly random binary string of the requested length."""
    if length < 1:
        raise ValueError("length must be positive")
    return "".join(str(int(bit)) for bit in rng.integers(0, 2, size=length))


def random_hex_nonce(rng: np.random.Generator, length: int = 8) -> str:
    """Return a random hexadecimal nonce used for replay detection."""
    return "".join(str(int(digit)) for digit in rng.integers(0, 16, size=length))


def generate_key(rng: np.random.Generator, length: int) -> str:
    """Generate the sender/verifier shared signing key."""
    return random_bits(rng, length)


def generate_message(rng: np.random.Generator, length: int) -> str:
    """Generate a uniformly random message to sign."""
    return random_bits(rng, length)


def sign(transaction: QDSTransaction) -> SignatureBlock:
    """Prepare the signature qubits for ``transaction``.

    At position ``i`` the sender prepares the eigenstate ``|v_i>_sigma_i`` of
    the key-dictated basis ``sigma_i`` with signed value ``v_i = m_i XOR k_i``.
    These qubits are what the quantum channel distributes.
    """
    qubits = tuple(
        pauli_eigenstate(transaction.signed_values[i], transaction.basis_at(i))
        for i in range(transaction.length)
    )
    return SignatureBlock(transaction=transaction, qubits=qubits)


def make_transaction(
    rng: np.random.Generator,
    length: int,
    sender_id: str = "alice",
    verifier_id: str = "victor",
    requesting_entity: str | None = None,
    authorised: bool = True,
) -> QDSTransaction:
    """Create a transaction with a fresh message, key and nonce."""
    message = generate_message(rng, length)
    key = generate_key(rng, length)
    nonce = random_hex_nonce(rng)
    entity = requesting_entity if requesting_entity is not None else sender_id
    return QDSTransaction(
        message=message,
        key=key,
        nonce=nonce,
        sender_id=sender_id,
        verifier_id=verifier_id,
        requesting_entity=entity,
        authorised=authorised,
    )


__all__: list[str] = [
    "generate_key",
    "generate_message",
    "make_transaction",
    "random_bits",
    "random_hex_nonce",
    "sign",
]
