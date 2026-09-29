"""UC-5 - interference with the simulated quantum channel."""

from __future__ import annotations

from ..channel import Disturbance
from .base import (
    ATTACK_CHANNEL,
    ATTACK_TITLES,
    Attack,
    AttackContext,
    AttackOutcome,
)


class ChannelManipulation(Attack):
    """Disturb the transport rather than the protocol logic.

    All three channels of the prototype can be attacked, and they are *not*
    equally powerful - a distinction the evaluation relies on:

    ``quantum_fraction``
        a random non-identity Pauli error on a fraction of the transmitted
        copies.  Every non-identity Pauli anticommutes with the target Pauli
        half the time, but because the copy starts in an eigenstate an
        anticommuting Pauli always flips the eigenvalue, so this channel flips
        the target with probability 1.
    ``classical_fraction``
        forged teleportation bits, so the receiver applies the wrong Pauli
        correction.  The resulting error is a *random* non-identity Pauli, which
        flips the target eigenvalue only half the time - a weaker attack that a
        careless implementation would score identically to the direct one.
    ``loss_fraction``
        qubits intercepted and never returned.  A per-qubit measurement cannot
        notice an absent qubit, so this is caught by counting copies, not by
        measuring them.
    ``witness_fraction``
        retained Bell pairs disturbed, which degrades the two-body correlators
        the Pauli-measurement detector relies on.
    """

    key = ATTACK_CHANNEL
    title = ATTACK_TITLES[ATTACK_CHANNEL]
    description = (
        "Adversary injects Pauli errors, forges classical teleportation bits, "
        "and disturbs the retained entanglement witness."
    )

    def __init__(
        self,
        quantum_fraction: float = 1.0,
        classical_fraction: float = 0.5,
        loss_fraction: float = 0.0,
        witness_fraction: float = 0.5,
    ) -> None:
        for name, value in (
            ("quantum_fraction", quantum_fraction),
            ("classical_fraction", classical_fraction),
            ("loss_fraction", loss_fraction),
            ("witness_fraction", witness_fraction),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")
        self.quantum_fraction = quantum_fraction
        self.classical_fraction = classical_fraction
        self.loss_fraction = loss_fraction
        self.witness_fraction = witness_fraction

    def disturbances(self) -> tuple[Disturbance, ...]:
        """Return the channel disturbances this attack injects."""
        selected: list[Disturbance] = []
        if self.quantum_fraction > 0.0:
            selected.append(Disturbance("pauli_decoherence", self.quantum_fraction))
        if self.classical_fraction > 0.0:
            selected.append(Disturbance("classical_tamper", self.classical_fraction))
        if self.loss_fraction > 0.0:
            selected.append(Disturbance("photon_loss", self.loss_fraction))
        if 0.0 < self.witness_fraction < 1.0:
            selected.append(Disturbance("witness_disturbance", self.witness_fraction))
        return tuple(selected)

    def run(self, context: AttackContext) -> AttackOutcome:
        """Return the disturbances to apply during distribution."""
        return self._outcome(
            context,
            disturbances=self.disturbances(),
            notes=(
                f"Pauli errors on {self.quantum_fraction:.0%} of copies, forged "
                f"classical teleportation bits on {self.classical_fraction:.0%}, "
                f"{self.loss_fraction:.0%} of copies dropped, and "
                f"{self.witness_fraction:.0%} of witness pairs disturbed."
            ),
        )
