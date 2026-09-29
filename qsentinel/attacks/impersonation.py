"""UC-2 - impersonation of a legitimate sender."""

from __future__ import annotations

from dataclasses import replace

from ..protocol.sender import random_bits
from ..protocol.sender import sign
from .base import (
    ATTACK_IMPERSONATION,
    ATTACK_TITLES,
    Attack,
    AttackContext,
    AttackOutcome,
)


class Impersonation(Attack):
    """Present an attacker's own well-formed signature as the real sender's.

    Unlike forgery, the impersonator holds a *well-formed* key - their own -
    and additionally relabels the sender identity.  The resulting quantum
    signature is internally consistent, but it is inconsistent with the key
    the verifier shares with the genuine sender, so the mismatch concentrates
    exactly on the positions where the two keys differ.

    This distinction matters for the report: a forgery is caught because the
    adversary's states are random noise, whereas an impersonation is caught
    because a *valid* signature is bound to the wrong key.
    """

    key = ATTACK_IMPERSONATION
    title = ATTACK_TITLES[ATTACK_IMPERSONATION]
    description = (
        "Adversary presents a well-formed signature made with their own key and "
        "relabels the transaction as coming from the legitimate sender."
    )

    def __init__(self, attacker_id: str = "mallory") -> None:
        if not attacker_id:
            raise ValueError("attacker_id must be non-empty")
        self.attacker_id = attacker_id

    def run(self, context: AttackContext) -> AttackOutcome:
        """Return a signature made with the attacker's key, spoofing the sender."""
        transaction = context.transaction
        attacker_key = random_bits(context.rng, transaction.length)
        mismatched = sum(
            1 for real, fake in zip(transaction.key, attacker_key) if real != fake
        )
        spoofed = replace(transaction, key=attacker_key)
        return self._outcome(
            context,
            transaction=spoofed,
            signature_override=sign(spoofed),
            notes=(
                f"'{self.attacker_id}' submitted a signature bound to their own "
                f"key while claiming to be '{transaction.sender_id}'. The key "
                f"differs on {mismatched} of {transaction.length} positions, so "
                "those qubits are eigenstates of the wrong Pauli operator."
            ),
        )
