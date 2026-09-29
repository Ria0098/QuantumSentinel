"""End-to-end transaction runner.

One :meth:`QDSSession.run_scenario` call executes the complete required flow::

    Sender -> Quantum Channel -> Receiver -> Verifier -> Threat Detector

and returns a :class:`ScenarioResult` carrying the verification outcome, both
detector verdicts and every statistic they used.  The session owns the replay
cache and the authorisation set because both are properties of the *verifier's*
state across transactions, not of a single run.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .attacks import (
    ATTACK_BENIGN,
    Attack,
    AttackContext,
    AttackOutcome,
    BenignExchange,
    default_registry,
)
from .channel import QuantumChannel
from .config import ExperimentConfig
from .detection import DetectionEngine, DetectionReport, build_input
from .protocol import ReplayCache, make_transaction, sign
from .protocol.state import QDSTransaction
from .protocol.verifier import verify


@dataclass
class ScenarioResult:
    """Everything one scenario produced."""

    attack: str
    title: str
    is_attack: bool
    expected_quantum_visible: bool
    verification: Any
    detection: DetectionReport
    outcome: AttackOutcome
    elapsed_seconds: float
    authorised: bool = True
    rejected: bool = False
    notes: str = ""

    @property
    def accepted_by_protocol(self) -> bool:
        """Whether the protocol layer would accept the transaction."""
        return self.verification.accepted and not self.rejected

    def as_dict(self) -> dict[str, Any]:
        """JSON-friendly view of the whole scenario."""
        return {
            "attack": self.attack,
            "title": self.title,
            "is_attack": self.is_attack,
            "expected_quantum_visible": self.expected_quantum_visible,
            "accepted_by_protocol": self.accepted_by_protocol,
            "rejected": self.rejected,
            "authorised": self.authorised,
            "elapsed_seconds": self.elapsed_seconds,
            "notes": self.notes,
            "attack_outcome": self.outcome.as_dict(),
            "verification": self.verification.as_dict(),
            "detection": self.detection.as_dict(),
        }


class QDSSession:
    """Stateful driver for signing, distribution, verification and detection."""

    def __init__(
        self,
        config: ExperimentConfig | None = None,
        engine: DetectionEngine | None = None,
        attacks: dict[str, Attack] | None = None,
        sender_id: str = "alice",
        verifier_id: str = "victor",
    ) -> None:
        self.config = config or ExperimentConfig()
        self.engine = engine or DetectionEngine()
        self.attacks = attacks or default_registry()
        self.replay_cache = ReplayCache(self.config.detection.replay_cache_size)
        self.authorised_entities = frozenset({sender_id, verifier_id})
        self.sender_id = sender_id
        self.verifier_id = verifier_id
        self._accepted: list[QDSTransaction] = []
        self._counter = 0

    @property
    def accepted_history(self) -> tuple[QDSTransaction, ...]:
        """Transactions this verifier has already accepted."""
        return tuple(self._accepted)

    def new_transaction(self, rng: np.random.Generator | None = None) -> QDSTransaction:
        """Create a fresh transaction with a new message, key and nonce."""
        generator = rng if rng is not None else self.config.rng(self._counter)
        self._counter += 1
        return make_transaction(
            generator,
            self.config.protocol.message_length,
            sender_id=self.sender_id,
            verifier_id=self.verifier_id,
        )

    def run_scenario(
        self,
        attack_key: str = ATTACK_BENIGN,
        seed_offset: int | None = None,
        transaction: QDSTransaction | None = None,
    ) -> ScenarioResult:
        """Execute one scenario end to end and return its result."""
        if attack_key not in self.attacks:
            raise KeyError(
                f"unknown attack {attack_key!r}; available: {sorted(self.attacks)}"
            )
        offset = self._counter if seed_offset is None else seed_offset
        rng = self.config.rng(offset)
        self._counter += 1

        txn = transaction if transaction is not None else self.new_transaction(rng)
        attack = self.attacks[attack_key]
        context = AttackContext(
            transaction=txn,
            config=self.config,
            rng=rng,
            replay_cache=self.replay_cache,
            authorised_entities=self.authorised_entities,
            accepted_history=self.accepted_history,
        )
        outcome = attack.run(context)
        started = time.perf_counter()

        submitted = outcome.transaction
        block = outcome.signature_override or sign(submitted)

        channel = QuantumChannel(self.config.protocol, self.config.channel, rng)
        reference = outcome.reference or txn
        distributed = channel.transmit(block, outcome.disturbances, reference=reference)

        freshness_ok = self.replay_cache.is_fresh(submitted)
        verification = verify(distributed, self.config.protocol, rng, freshness_ok)

        detection_input = build_input(
            verification,
            self.config.detection,
            self.authorised_entities,
            context_notes={"attack": attack_key},
        )
        detection = self.engine.run(detection_input)

        accepted = verification.accepted
        if accepted:
            self.replay_cache.remember(submitted)
            self._accepted.append(submitted)
        elapsed = time.perf_counter() - started

        return ScenarioResult(
            attack=attack_key,
            title=outcome.title,
            is_attack=not isinstance(attack, BenignExchange),
            expected_quantum_visible=outcome.expected_quantum_visible,
            verification=verification,
            detection=detection,
            outcome=outcome,
            elapsed_seconds=elapsed,
            authorised=submitted.authorised,
            rejected=not accepted,
            notes=outcome.notes,
        )

    def run_all(
        self, attack_keys: tuple[str, ...] | None = None
    ) -> list[ScenarioResult]:
        """Run every scenario in order, returning the results."""
        keys = attack_keys or tuple(self.attacks)
        return [self.run_scenario(key) for key in keys]

    def reset(self) -> None:
        """Clear the replay cache and accepted history."""
        self.replay_cache.clear()
        self._accepted.clear()
        self._counter = 0
