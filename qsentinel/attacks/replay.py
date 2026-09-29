"""UC-3 - replay of a previously accepted transaction."""

from __future__ import annotations

from dataclasses import replace

from ..protocol.sender import sign
from .base import ATTACK_REPLAY, ATTACK_TITLES, Attack, AttackContext, AttackOutcome


class ReplayAttack(Attack):
    """Re-submit a transaction that was already accepted.

    The adversary reuses the message, key and nonce of a previously accepted
    transaction, so the entire quantum transcript is *bit-identical* to the
    original: every Pauli expectation value is reproduced exactly and every
    measurement outcome matches.  No measurement-based detector can see this
    attack, which is precisely why the protocol needs a classical freshness
    mechanism and why ``expected_quantum_visible`` is ``False``.

    The evaluation reports the measured outcome against that expectation, so
    the report shows an honest false negative for the Pauli-measurement layer
    rather than a convenient 100% detection rate.
    """

    key = ATTACK_REPLAY
    title = ATTACK_TITLES[ATTACK_REPLAY]
    description = (
        "Adversary re-submits a previously accepted transaction, reusing its "
        "message, key and nonce."
    )
    expected_quantum_visible = False

    def run(self, context: AttackContext) -> AttackOutcome:
        """Return the previously accepted transaction, unchanged."""
        if not context.accepted_history:
            raise RuntimeError(
                "replay attack requires at least one accepted transaction in history"
            )
        original = context.accepted_history[-1]
        replayed = replace(original)
        return self._outcome(
            context,
            transaction=replayed,
            signature_override=sign(replayed),
            reference=replayed,
            notes=(
                f"Replayed transaction {original.transaction_id} (nonce "
                f"{original.nonce}). The quantum transcript is identical to the "
                "original, so only the classical freshness check can see it."
            ),
        )
