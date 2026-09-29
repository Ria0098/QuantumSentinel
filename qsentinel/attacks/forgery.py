"""UC-1 - digital signature forgery."""

from __future__ import annotations

from dataclasses import replace

from ..protocol.sender import sign
from .base import (
    ATTACK_FORGERY,
    ATTACK_TITLES,
    Attack,
    AttackContext,
    AttackOutcome,
)


class SignatureForgery(Attack):
    """Forge signature material without possessing the signing key.

    The adversary knows the message and the protocol but *not* the sender's
    key ``k``.  It guesses a key ``k'`` that agrees with the real one on a
    configurable fraction of positions and signs the message with it.  At every
    position where the guess is wrong, the forged signature qubit is the
    eigenstate of the wrong Pauli observable, so the verifier's per-copy
    measurements disagree with the intended eigenvalues.

    ``guess_accuracy = 1.0`` is the degenerate "perfect guess" case, which is
    exactly the situation an unbounded adversary would create; the default of
    ``0.5`` models an adversary that recovers half the key.
    """

    key = ATTACK_FORGERY
    title = ATTACK_TITLES[ATTACK_FORGERY]
    description = (
        "Adversary signs the message with a guessed key that matches the real "
        "key on only a fraction of positions."
    )

    def __init__(self, guess_accuracy: float = 0.5) -> None:
        if not 0.0 <= guess_accuracy <= 1.0:
            raise ValueError("guess_accuracy must lie in [0, 1]")
        self.guess_accuracy = guess_accuracy

    def run(self, context: AttackContext) -> AttackOutcome:
        """Return a forged signature block built from the guessed key."""
        transaction = context.transaction
        length = transaction.length
        correct = int(round(self.guess_accuracy * length))
        guess = list(transaction.key)
        for index in range(correct, length):
            guess[index] = "1" if guess[index] == "0" else "0"
        forged = replace(transaction, key="".join(guess))
        wrong = length - correct
        return self._outcome(
            context,
            signature_override=sign(forged),
            notes=(
                f"Guessed {correct}/{length} key bits correctly. At the remaining "
                f"{wrong} positions the forged qubit is an eigenstate of the wrong "
                "Pauli operator, so the verifier's own-basis measurement returns a "
                "random +-1 with probability 1."
            ),
        )
