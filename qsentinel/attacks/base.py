"""Shared scaffolding for the attack simulations.

Attack *generation* lives in :mod:`qsentinel.attacks` and produces a
declarative :class:`AttackOutcome`: a possibly-swapped transaction, a
possibly-forged signature block, and a list of channel disturbances.  The
protocol layer in :mod:`qsentinel.protocol` and the channel in
:mod:`qsentinel.channel` never import this package, so adding a new attack
never requires touching protocol logic.

The five attack classes live in sibling modules and match the threat
categories named in the SIH problem statement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ..channel import Disturbance
from ..config import ExperimentConfig
from ..protocol.freshness import ReplayCache
from ..protocol.state import QDSTransaction, SignatureBlock

ATTACK_BENIGN = "legitimate"
ATTACK_FORGERY = "forgery"
ATTACK_IMPERSONATION = "impersonation"
ATTACK_REPLAY = "replay"
ATTACK_UNAUTHORIZED = "unauthorized_verification"
ATTACK_CHANNEL = "channel_manipulation"

ATTACK_ORDER: tuple[str, ...] = (
    ATTACK_BENIGN,
    ATTACK_FORGERY,
    ATTACK_IMPERSONATION,
    ATTACK_REPLAY,
    ATTACK_UNAUTHORIZED,
    ATTACK_CHANNEL,
)

ATTACK_TITLES: dict[str, str] = {
    ATTACK_BENIGN: "Legitimate transaction",
    ATTACK_FORGERY: "Signature forgery",
    ATTACK_IMPERSONATION: "Sender impersonation",
    ATTACK_REPLAY: "Replay attack",
    ATTACK_UNAUTHORIZED: "Unauthorized verification attempt",
    ATTACK_CHANNEL: "Quantum channel manipulation",
}


@dataclass
class AttackContext:
    """Everything an attack may read while it is being constructed."""

    transaction: QDSTransaction
    config: ExperimentConfig
    rng: np.random.Generator
    replay_cache: ReplayCache
    authorised_entities: frozenset[str]
    accepted_history: tuple[QDSTransaction, ...] = field(default=())


@dataclass(frozen=True)
class AttackOutcome:
    """What the adversary did, in a form the protocol layer can execute.

    ``expected_quantum_visible`` records whether the *ground truth* of this
    attack is, in principle, observable in the Pauli measurement statistics.
    It is ``False`` for replay and unauthorised verification, and the
    evaluation reports the measured outcome against that expectation.
    """

    attack: str
    title: str
    description: str
    transaction: QDSTransaction
    disturbances: tuple[Disturbance, ...] = ()
    signature_override: SignatureBlock | None = None
    reference: QDSTransaction | None = None
    expected_quantum_visible: bool = True
    notes: str = ""

    @property
    def rewrites_signature(self) -> bool:
        """True when the adversary supplied its own signature block."""
        return self.signature_override is not None

    @property
    def swaps_reference(self) -> bool:
        """True when the attacker also changes which record the verifier trusts.

        Only a replay does this: re-submitting an old transaction means the
        verifier is being asked about a transaction it already holds a record
        of, and it is the freshness cache - not the quantum data - that must
        reject it.
        """
        return self.reference is not None

    def as_dict(self) -> dict[str, Any]:
        """JSON-friendly view used by the reporting layer."""
        return {
            "attack": self.attack,
            "title": self.title,
            "description": self.description,
            "expected_quantum_visible": self.expected_quantum_visible,
            "notes": self.notes,
            "disturbances": [d.as_dict() for d in self.disturbances],
            "rewrites_signature": self.rewrites_signature,
            "swaps_reference": self.swaps_reference,
        }


class Attack(ABC):
    """Base class for every simulated attack."""

    key: str = ""
    title: str = ""
    description: str = ""
    expected_quantum_visible: bool = True

    @abstractmethod
    def run(self, context: AttackContext) -> AttackOutcome:
        """Produce the adversary's modifications for one transaction."""

    def _outcome(self, context: AttackContext, **kwargs: Any) -> AttackOutcome:
        """Build an outcome pre-filled with this attack's identity.

        The transaction defaults to the context's, but an attack that swaps it
        (impersonation, replay) passes its own.
        """
        kwargs.setdefault("transaction", context.transaction)
        return AttackOutcome(
            attack=self.key,
            title=self.title,
            description=self.description,
            expected_quantum_visible=self.expected_quantum_visible,
            **kwargs,
        )

    def __repr__(self) -> str:
        return f"{type(self).__name__}(key={self.key!r})"


class BenignExchange(Attack):
    """The attack-free reference execution required by FR-16."""

    key = ATTACK_BENIGN
    title = ATTACK_TITLES[ATTACK_BENIGN]
    description = (
        "Honest sender, honest channel, honest verifier. No adversarial action "
        "is taken, so any alarm raised here is a false positive."
    )
    expected_quantum_visible = False

    def run(self, context: AttackContext) -> AttackOutcome:
        """Return the untouched transaction."""
        return self._outcome(
            context,
            notes="No disturbance applied. This is the false-alarm baseline.",
        )
