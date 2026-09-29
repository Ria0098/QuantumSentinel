"""UC-4 - verification requested by an unauthorised entity."""

from __future__ import annotations

from dataclasses import replace

from .base import (
    ATTACK_UNAUTHORIZED,
    ATTACK_TITLES,
    Attack,
    AttackContext,
    AttackOutcome,
)


class UnauthorizedVerification(Attack):
    """Attempt verification from outside the authorised context.

    No quantum state is touched.  The signature is genuine, every copy is
    perfect, and every measurement agrees - the only anomaly is that the
    requesting entity is not the party the protocol authorises to verify.

    This is a context failure rather than a state failure, so it is invisible
    to the Pauli-measurement detector by construction.  The authorisation rule
    is part of the *statistical* detector's composite rule set, which is why
    the two layers disagree on this scenario in the evaluation table.
    """

    key = ATTACK_UNAUTHORIZED
    title = ATTACK_TITLES[ATTACK_UNAUTHORIZED]
    description = (
        "A genuine, unmodified transaction is submitted for verification by an "
        "entity the protocol does not authorise to verify."
    )
    expected_quantum_visible = False

    def __init__(self, intruder_id: str = "eve") -> None:
        if not intruder_id:
            raise ValueError("intruder_id must be non-empty")
        self.intruder_id = intruder_id

    def run(self, context: AttackContext) -> AttackOutcome:
        """Return the untouched transaction with an unauthorised requester."""
        unauthorised = replace(
            context.transaction,
            requesting_entity=self.intruder_id,
            authorised=False,
        )
        return self._outcome(
            context,
            transaction=unauthorised,
            notes=(
                f"'{self.intruder_id}' requested verification but is not in the "
                f"authorised set {sorted(context.authorised_entities)}. The "
                "quantum state is untouched."
            ),
        )
