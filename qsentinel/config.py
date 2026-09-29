"""Single source of truth for every tunable value in the prototype.

The PRD requires that thresholds are not duplicated across modules, so all
configuration lives here and every layer takes its settings from these
dataclasses.  Every field carries a documented default and a short rationale
so the Word report can quote measured operating points instead of guesses.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

DEFAULT_SEED = 20260101


@dataclass(frozen=True)
class ProtocolConfig:
    """Structural parameters of the qubit-wise QDS protocol.

    Attributes
    ----------
    message_length:
        Number of bits ``L`` in the signed message.
    copies_per_bit:
        Number ``n`` of teleportation copies distributed per message bit.
        Each copy is an independent test qubit, so an error must coincide across
        copies to escape every check.
    witness_pairs:
        Number of Bell pairs retained (never consumed by teleportation) and
        handed to the Pauli-measurement detector as an entanglement witness.
    parity_group_size:
        Group size ``g`` for the distillable-amplification check: the product
        (cat-state) observable ``sigma (x) ... (x) sigma`` is measured over
        ``g`` test qubits drawn from the *same* message position.  A parity
        check detects any *odd* number of errors inside its group with
        probability 1, which is the amplification this prototype relies on.
        ``g = 1`` reduces the scheme to independent single-qubit checks.
    sign_bit:
        Bit whose value fixes the shared Bell resource as
        ``|Phi(bit)> = (|0,0> + (-1)**bit |1,1>) / sqrt(2)``.  ``0`` selects
        the usual ``|Phi+>`` resource.
    """

    message_length: int = 8
    copies_per_bit: int = 4
    witness_pairs: int = 8
    parity_group_size: int = 2
    sign_bit: int = 0

    def __post_init__(self) -> None:
        if self.message_length < 1:
            raise ValueError("message_length must be positive")
        if self.copies_per_bit < 1:
            raise ValueError("copies_per_bit must be positive")
        if self.witness_pairs < 0:
            raise ValueError("witness_pairs must be non-negative")
        if self.parity_group_size < 1:
            raise ValueError("parity_group_size must be positive")
        if self.parity_group_size > self.copies_per_bit:
            raise ValueError("parity_group_size cannot exceed copies_per_bit")
        if self.sign_bit not in (0, 1):
            raise ValueError("sign_bit must be 0 or 1")

    @property
    def test_qubit_count(self) -> int:
        """Total number of teleportation copies in one transaction."""
        return self.message_length * self.copies_per_bit

    @property
    def parity_group_count(self) -> int:
        """Number of distillation groups per transaction."""
        per_position = self.copies_per_bit // self.parity_group_size
        return self.message_length * per_position

    @property
    def sign_lambda(self) -> int:
        """The Bell resource eigenvalue as ``+/-1``."""
        return 1 if self.sign_bit == 0 else -1

    def with_group_size(self, group_size: int) -> "ProtocolConfig":
        """Return a copy using a different distillation group size."""
        return replace(self, parity_group_size=group_size)


@dataclass(frozen=True)
class ChannelConfig:
    """Physical noise model of the simulated quantum + classical channels.

    ``decoherence`` is modelled as a Pauli channel: every transmitted test
    qubit independently suffers a non-identity Pauli error with probability
    ``decoherence_rate``.  ``message_tamper_rate`` corrupts the two classical
    teleportation bits, which makes the receiver apply the wrong Pauli
    correction.  ``loss_rate`` replaces a qubit by the maximally mixed state,
    modelling photon loss.
    """

    decoherence_rate: float = 0.0
    message_tamper_rate: float = 0.0
    loss_rate: float = 0.0

    def __post_init__(self) -> None:
        for name in ("decoherence_rate", "message_tamper_rate", "loss_rate"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")

    @property
    def is_noiseless(self) -> bool:
        """True when the channel applies no disturbance of any kind."""
        return (
            self.decoherence_rate == 0.0
            and self.message_tamper_rate == 0.0
            and self.loss_rate == 0.0
        )


@dataclass(frozen=True)
class DetectionConfig:
    """Decision thresholds for both detection layers.

    All thresholds are *fixed constants chosen from the analytical behaviour
    of the protocol*, never fitted to the attack data and never learned.  The
    operating point targets a false-alarm rate near 1% for a channel with
    ``decoherence_rate <= 0.01`` while still reacting to single-qubit attacks.
    """

    mismatch_threshold: float = 0.05
    qber_threshold: float = 0.02
    per_basis_qber_threshold: float = 0.05
    distribution_distance_threshold: float = 0.20
    correlator_agreement_threshold: float = 0.90
    parity_expectation_threshold: float = 0.90
    replay_cache_size: int = 512

    def __post_init__(self) -> None:
        for name in (
            "mismatch_threshold",
            "qber_threshold",
            "per_basis_qber_threshold",
            "distribution_distance_threshold",
            "parity_expectation_threshold",
        ):
            if not 0.0 <= getattr(self, name) <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")
        if not 0.0 <= self.correlator_agreement_threshold <= 1.0:
            raise ValueError("correlator_agreement_threshold must lie in [0, 1]")
        if self.replay_cache_size < 1:
            raise ValueError("replay_cache_size must be positive")


@dataclass(frozen=True)
class ExperimentConfig:
    """Top-level configuration passed to every layer of the prototype."""

    seed: int = DEFAULT_SEED
    protocol: ProtocolConfig = field(default_factory=ProtocolConfig)
    channel: ChannelConfig = field(default_factory=ChannelConfig)
    detection: DetectionConfig = field(default_factory=DetectionConfig)

    def rng(self, offset: int = 0) -> Any:
        """Return a seeded generator; ``offset`` decorrelates derived streams."""
        import numpy as np

        return np.random.default_rng(self.seed + offset)

    def seeded(self, seed: int) -> "ExperimentConfig":
        """Return a copy using a different top-level seed."""
        return replace(self, seed=seed)

    def describe(self) -> dict[str, Any]:
        """JSON-friendly summary used by the report generator."""
        return {
            "seed": self.seed,
            "protocol": {
                "message_length": self.protocol.message_length,
                "copies_per_bit": self.protocol.copies_per_bit,
                "witness_pairs": self.protocol.witness_pairs,
                "parity_group_size": self.protocol.parity_group_size,
                "test_qubit_count": self.protocol.test_qubit_count,
                "parity_group_count": self.protocol.parity_group_count,
            },
            "channel": {
                "decoherence_rate": self.channel.decoherence_rate,
                "message_tamper_rate": self.channel.message_tamper_rate,
                "loss_rate": self.channel.loss_rate,
            },
            "detection": {
                "mismatch_threshold": self.detection.mismatch_threshold,
                "qber_threshold": self.detection.qber_threshold,
                "per_basis_qber_threshold": self.detection.per_basis_qber_threshold,
                "distribution_distance_threshold": (
                    self.detection.distribution_distance_threshold
                ),
                "correlator_agreement_threshold": (
                    self.detection.correlator_agreement_threshold
                ),
                "parity_expectation_threshold": (
                    self.detection.parity_expectation_threshold
                ),
            },
        }


#: Configurations that are useful to show in the report / demo.
PRESETS: dict[str, ExperimentConfig] = {
    "clean": ExperimentConfig(),
    "noisy": ExperimentConfig(channel=ChannelConfig(decoherence_rate=0.01)),
    "degraded": ExperimentConfig(channel=ChannelConfig(decoherence_rate=0.05)),
    "unamplified": ExperimentConfig(
        protocol=ProtocolConfig(parity_group_size=1), channel=ChannelConfig()
    ),
}

#: Every named preset, without the bikeshed of case.
presets: dict[str, ExperimentConfig] = PRESETS
