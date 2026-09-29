"""The simulated quantum channel and the disturbances an adversary can inject.

The channel is the only place where protocol information moves, so it is also
the only place where an attack or a physical-noise model may act.  It consumes
an explicit tuple of :class:`Disturbance` objects rather than importing
:mod:`qsentinel.attacks`, which keeps attack *generation* strictly separate
from protocol *execution*.

Two channels are modelled:

* the **quantum channel**, which distributes each signature qubit by
  teleporting it through a fresh Bell pair, and may suffer Pauli decoherence
  or photon loss;
* the **classical control channel**, which carries the two teleportation bits
  and may be tampered with, causing the receiver to apply the wrong correction.

An adversary acting only on the classical channel flips the receiver's qubit
with probability 1/2 (a random non-identity Pauli anticommutes with the target
Pauli half the time); an adversary acting on the quantum channel flips it with
probability 1.  Modelling that difference honestly is what keeps the
channel-manipulation benchmark from being trivially easy.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .config import ChannelConfig, ProtocolConfig
from .quantum.gates import PAULI
from .quantum.states import NON_TRIVIAL_PAULIS, bell_pair, pauli_eigenstate
from .protocol.state import (
    DistributedState,
    QDSTransaction,
    SignatureBlock,
    TestQubit,
    WitnessPair,
)
from .protocol.teleportation import teleport

DISTURBANCE_KINDS: tuple[str, ...] = (
    "pauli_decoherence",
    "classical_tamper",
    "photon_loss",
    "signature_substitution",
    "witness_disturbance",
)


@dataclass(frozen=True)
class Disturbance:
    """A declarative instruction for the adversary or for the noise model.

    Attributes
    ----------
    kind:
        One of :data:`DISTURBANCE_KINDS`.
    intensity:
        Fraction in ``[0, 1]`` of the transmitted copies to hit.  For
        ``"signature_substitution"`` it is instead a *count* of message
        positions to corrupt.
    targets:
        Optional explicit ``(position, copy_index)`` pairs.  When empty the
        channel applies the disturbance to a uniformly random subset of the
        requested size.
    """

    kind: str
    intensity: float = 1.0
    targets: tuple[tuple[int, int], ...] = field(default=())

    def __post_init__(self) -> None:
        if self.kind not in DISTURBANCE_KINDS:
            raise ValueError(
                f"unknown disturbance {self.kind!r}; expected one of {DISTURBANCE_KINDS}"
            )
        floor = 0.0
        ceiling = 1e9 if self.kind == "signature_substitution" else 1.0
        if not floor <= self.intensity <= ceiling:
            raise ValueError(f"disturbance intensity out of range for {self.kind!r}")

    @property
    def is_count_based(self) -> bool:
        """True when ``intensity`` is a number of positions rather than a fraction."""
        return self.kind == "signature_substitution"

    def as_dict(self) -> dict[str, object]:
        """JSON-friendly view of the disturbance."""
        return {
            "kind": self.kind,
            "intensity": self.intensity,
            "targets": [list(target) for target in self.targets],
        }


class QuantumChannel:
    """Distributes a :class:`SignatureBlock` to a simulated receiver."""

    def __init__(
        self,
        protocol: ProtocolConfig,
        channel: ChannelConfig,
        rng: np.random.Generator,
    ) -> None:
        self.protocol = protocol
        self.channel = channel
        self.rng = rng

    @property
    def sign_lambda(self) -> int:
        """Eigenvalue of the shared Bell resource."""
        return self.protocol.sign_lambda

    def physical_disturbances(self) -> tuple[Disturbance, ...]:
        """Translate the channel noise model into explicit disturbances.

        Physical noise and adversarial activity are expressed with the same
        vocabulary so that the detectors cannot tell them apart by
        construction - which is what makes the false-alarm benchmark honest.
        """
        disturbances: list[Disturbance] = []
        if self.channel.decoherence_rate > 0.0:
            disturbances.append(
                Disturbance("pauli_decoherence", self.channel.decoherence_rate)
            )
        if self.channel.message_tamper_rate > 0.0:
            disturbances.append(
                Disturbance("classical_tamper", self.channel.message_tamper_rate)
            )
        if self.channel.loss_rate > 0.0:
            disturbances.append(Disturbance("photon_loss", self.channel.loss_rate))
        return tuple(disturbances)

    def transmit(
        self,
        block: SignatureBlock,
        disturbances: tuple[Disturbance, ...] = (),
        reference: QDSTransaction | None = None,
    ) -> DistributedState:
        """Teleport every signature qubit, then apply noise and attack disturbances.

        ``block`` is what the sender claims to have signed.  ``reference`` is
        the transaction the *verifier* holds a record of - its own copy of the
        message, key and nonce.  The per-copy measurement basis and expected
        eigenvalue are taken from ``reference``, never from ``block``, which is
        what stops an attacker who submits a self-consistent forged transaction
        from verifying against its own expectations.
        """
        transaction = block.transaction
        trusted = reference if reference is not None else transaction
        length = trusted.length
        copies = self.protocol.copies_per_bit
        total = length * copies

        combined = self.physical_disturbances() + disturbances
        pauli_targets = self._target_set("pauli_decoherence", combined, total, length, copies)
        tamper_targets = self._target_set("classical_tamper", combined, total, length, copies)
        loss_targets = self._target_set("photon_loss", combined, total, length, copies)
        substitution = self._substitution(combined)
        substituted_positions = self._substituted_positions(substitution, length)

        test_qubits: list[TestQubit] = []
        transcript: list[tuple[int, int]] = []
        dropped = 0
        substituted = False

        for position in range(length):
            basis = trusted.basis_at(position)
            expected = trusted.expected_eigenvalue_at(position)
            payload = block.qubits[position]
            if position in substituted_positions:
                payload = _flipped_eigenstate(expected, basis)
                substituted = True
            for copy_index in range(copies):
                key = (position, copy_index)
                if key in loss_targets:
                    dropped += 1
                    continue
                received, record = teleport(
                    payload,
                    bell_pair(self.sign_lambda, basis),
                    self.rng,
                    tamper=key in tamper_targets,
                )
                if key in pauli_targets:
                    received = _apply_random_pauli(received, self.rng)
                transcript.append(record.used_message)
                test_qubits.append(
                    TestQubit(
                        position=position,
                        copy_index=copy_index,
                        basis=basis,
                        expected_eigenvalue=expected,
                        state=received,
                        record=record,
                    )
                )

        return DistributedState(
            transaction=transaction,
            test_qubits=tuple(test_qubits),
            witness_pairs=self._build_witnesses(combined),
            classical_transcript=tuple(transcript),
            dropped_qubits=dropped,
            signature_substituted=substituted,
        )

    def _target_set(
        self,
        kind: str,
        disturbances: tuple[Disturbance, ...],
        total: int,
        length: int,
        copies: int,
    ) -> set[tuple[int, int]]:
        targets: set[tuple[int, int]] = set()
        for disturbance in disturbances:
            if disturbance.kind != kind:
                continue
            if disturbance.targets:
                targets.update(disturbance.targets)
                continue
            wanted = int(round(disturbance.intensity * total))
            if wanted <= 0:
                continue
            if wanted >= total:
                for position in range(length):
                    for copy_index in range(copies):
                        targets.add((position, copy_index))
                continue
            positions = self.rng.integers(0, length, size=wanted)
            copy_indices = self.rng.integers(0, copies, size=wanted)
            for position, copy_index in zip(positions, copy_indices):
                targets.add((int(position), int(copy_index)))
        return targets

    def _substitution(self, disturbances: tuple[Disturbance, ...]) -> Disturbance | None:
        for disturbance in disturbances:
            if disturbance.kind == "signature_substitution":
                return disturbance
        return None

    def _substituted_positions(
        self, disturbance: Disturbance | None, length: int
    ) -> set[int]:
        if disturbance is None:
            return set()
        count = min(int(disturbance.intensity), length)
        if count <= 0:
            return set()
        return {int(value) for value in self.rng.choice(length, size=count, replace=False)}

    def _build_witnesses(
        self, disturbances: tuple[Disturbance, ...]
    ) -> tuple[WitnessPair, ...]:
        count = self.protocol.witness_pairs
        if count <= 0:
            return ()
        fraction = 0.0
        for disturbance in disturbances:
            if disturbance.kind == "witness_disturbance":
                fraction = max(fraction, disturbance.intensity)
        pairs: list[WitnessPair] = []
        for index in range(count):
            basis = "Z" if index % 2 == 0 else "X"
            state = bell_pair(self.sign_lambda, basis)
            disturbed = False
            if fraction > 0.0 and self.rng.random() < fraction:
                state = _apply_random_pauli(state, self.rng)
                disturbed = True
            pairs.append(
                WitnessPair(
                    index=index,
                    basis=basis,
                    expected_eigenvalue=self.sign_lambda,
                    state=state,
                    disturbed=disturbed,
                )
            )
        return tuple(pairs)


def _apply_random_pauli(state, rng: np.random.Generator):
    pauli = NON_TRIVIAL_PAULIS[int(rng.integers(0, 3))]
    return state.apply_one_qubit(PAULI[pauli], 0)


def _flipped_eigenstate(expected_eigenvalue: int, basis: str):
    """Return the eigenstate with the *opposite* eigenvalue in ``basis``."""
    signed_value = (1 - expected_eigenvalue) // 2
    return pauli_eigenstate(1 - signed_value, basis)
