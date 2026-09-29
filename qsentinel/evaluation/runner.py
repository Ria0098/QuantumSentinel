"""Controlled experiments and metric computation.

The evaluation runs the same scenarios the CLI exposes, but many times, and
aggregates the ground-truth labels into confusion matrices per detector.  Two
sweeps are supported because they answer the two questions the PRD leaves open:

``run_evaluation``
    detection rate, false-alarm rate, accuracy and mean runtime per attack at
    a fixed operating point.
``run_noise_sweep``
    the same statistics as a function of the channel's decoherence rate, which
    is what locates the false-alarm knee and shows where the detector stops
    being usable.
``run_group_size_sweep``
    the same statistics as a function of the distillation group size, which
    measures what the amplify/verify step actually buys over independent
    per-copy checks.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field, replace
from typing import Any, Iterable, Sequence

from ..attacks import ATTACK_BENIGN, ATTACK_ORDER
from ..config import ExperimentConfig, ProtocolConfig
from ..session import QDSSession
from .metrics import ConfusionMatrix, mean, wilson_interval


@dataclass(frozen=True)
class TrialRecord:
    """One executed transaction, with its ground truth and both verdicts."""

    attack: str
    is_attack: bool
    statistical_verdict: bool
    pauli_verdict: bool
    protocol_accepted: bool
    verification_accepted: bool
    mismatch_rate: float
    elapsed_seconds: float

    def as_dict(self) -> dict[str, Any]:
        """JSON-friendly view of the trial."""
        return {
            "attack": self.attack,
            "is_attack": self.is_attack,
            "statistical_verdict": self.statistical_verdict,
            "pauli_verdict": self.pauli_verdict,
            "protocol_accepted": self.protocol_accepted,
            "verification_accepted": self.verification_accepted,
            "mismatch_rate": self.mismatch_rate,
            "elapsed_seconds": self.elapsed_seconds,
        }


@dataclass
class EvaluationResult:
    """Aggregated results of a controlled experiment."""

    trials: list[TrialRecord] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    label: str = ""

    def subset(self, attack: str) -> list[TrialRecord]:
        """Every trial belonging to one scenario."""
        return [trial for trial in self.trials if trial.attack == attack]

    def matrix(self, detector: str) -> ConfusionMatrix:
        """Confusion matrix for one detector over every trial."""
        attribute = _VERDICT_ATTRIBUTES[detector]
        tp = fp = tn = fn = 0
        for trial in self.trials:
            predicted = getattr(trial, attribute)
            if trial.is_attack and predicted:
                tp += 1
            elif trial.is_attack:
                fn += 1
            elif predicted:
                fp += 1
            else:
                tn += 1
        return ConfusionMatrix(tp, fp, tn, fn)

    def attack_rows(self) -> list[dict[str, Any]]:
        """Per-attack detection statistics for both detectors."""
        rows = []
        for attack in ATTACK_ORDER:
            subset = self.subset(attack)
            if not subset:
                continue
            attacks_present = subset[0].is_attack
            rows.append(
                {
                    "attack": attack,
                    "is_attack": attacks_present,
                    "trials": len(subset),
                    "statistical_detected": sum(
                        1 for t in subset if t.statistical_verdict
                    ),
                    "pauli_detected": sum(1 for t in subset if t.pauli_verdict),
                    "protocol_rejected": sum(
                        1 for t in subset if not t.protocol_accepted
                    ),
                    "mean_mismatch_rate": mean(t.mismatch_rate for t in subset),
                    "detection_rate": _rate(
                        sum(1 for t in subset if t.statistical_verdict), len(subset)
                    )
                    if attacks_present
                    else None,
                }
            )
        return rows

    def summary(self) -> dict[str, Any]:
        """Full JSON-friendly summary of the experiment."""
        return {
            "label": self.label,
            "config": self.config,
            "total_trials": len(self.trials),
            "statistical": self.matrix("statistical").as_dict(),
            "pauli_measurement": self.matrix("pauli_measurement").as_dict(),
            "per_attack": self.attack_rows(),
            "mean_runtime_seconds": mean(t.elapsed_seconds for t in self.trials),
            "total_runtime_seconds": sum(t.elapsed_seconds for t in self.trials),
        }


_VERDICT_ATTRIBUTES: dict[str, str] = {
    "statistical": "statistical_verdict",
    "pauli_measurement": "pauli_verdict",
}


def _rate(numerator: int, denominator: int) -> float:
    return 0.0 if denominator <= 0 else numerator / denominator


def _record_from_result(result) -> TrialRecord:
    return TrialRecord(
        attack=result.attack,
        is_attack=result.is_attack,
        statistical_verdict=result.detection.statistical.is_threat,
        pauli_verdict=result.detection.pauli.is_threat,
        protocol_accepted=result.accepted_by_protocol,
        verification_accepted=result.verification.accepted,
        mismatch_rate=float(result.verification.mismatch_rate()),
        elapsed_seconds=result.elapsed_seconds,
    )


def _seed_history(session: QDSSession, max_attempts: int = 100) -> None:
    """Ensure the session has at least one *accepted* transaction in history.

    The replay attack re-submits the most recently accepted transaction, so the
    evaluation must guarantee that one exists.  Under a noisy channel a benign
    run is sometimes rejected by the protocol; retry until one is accepted.
    """
    for _ in range(max_attempts):
        result = session.run_scenario(ATTACK_BENIGN)
        if result.accepted_by_protocol:
            return
    raise RuntimeError(
        f"could not obtain an accepted legitimate transaction after {max_attempts} attempts"
    )


def run_evaluation(
    config: ExperimentConfig | None = None,
    trials_per_attack: int = 50,
    attack_keys: Sequence[str] | None = None,
) -> EvaluationResult:
    """Run every scenario ``trials_per_attack`` times and aggregate the results."""
    base = config or ExperimentConfig()
    keys = tuple(attack_keys) if attack_keys else ATTACK_ORDER
    started = time.perf_counter()
    records: list[TrialRecord] = []

    for key in keys:
        for _ in range(trials_per_attack):
            session = QDSSession(base)
            if key == "replay":
                _seed_history(session)
            result = session.run_scenario(key)
            records.append(_record_from_result(result))

    return EvaluationResult(
        trials=records,
        config=base.describe(),
        label=f"trials_per_attack={trials_per_attack}",
    )


def run_noise_sweep(
    rates: Iterable[float],
    config: ExperimentConfig | None = None,
    trials_per_attack: int = 20,
    attack_keys: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    """Sweep the channel decoherence rate and report detection statistics."""
    base = config or ExperimentConfig()
    rows: list[dict[str, Any]] = []
    for rate in rates:
        noisy = replace(base, channel=replace(base.channel, decoherence_rate=rate))
        result = run_evaluation(noisy, trials_per_attack, attack_keys)
        statistical = result.matrix("statistical")
        pauli = result.matrix("pauli_measurement")
        rows.append(
            {
                "decoherence_rate": rate,
                "trials": len(result.trials),
                "statistical_detection_rate": statistical.detection_rate,
                "statistical_detection_rate_ci95": wilson_interval(
                    statistical.true_positives, statistical.positives
                ),
                "statistical_false_alarm_rate": statistical.false_alarm_rate,
                "statistical_false_alarm_ci95": wilson_interval(
                    statistical.false_positives, statistical.negatives
                ),
                "pauli_detection_rate": pauli.detection_rate,
                "pauli_false_alarm_rate": pauli.false_alarm_rate,
                "mean_runtime_seconds": mean(
                    t.elapsed_seconds for t in result.trials
                ),
            }
        )
    return rows


def run_group_size_sweep(
    group_sizes: Iterable[int],
    config: ExperimentConfig | None = None,
    trials_per_attack: int = 20,
    attack_keys: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    """Sweep the distillation group size and report what changes.

    ``parity_group_size = 1`` degenerates the check to independent per-copy
    verification; larger values measure the cat-state parity instead, which
    costs ``1 / g`` as many measurements.  The sweep reports the measured
    detection rate, the mean mismatch rate and the runtime for each setting so
    the report can state the trade-off from data rather than from theory.
    """
    base = config or ExperimentConfig()
    keys = tuple(attack_keys) if attack_keys else (ATTACK_BENIGN, "channel_manipulation")
    rows: list[dict[str, Any]] = []
    for size in group_sizes:
        protocol = ProtocolConfig(
            message_length=base.protocol.message_length,
            copies_per_bit=base.protocol.copies_per_bit,
            witness_pairs=base.protocol.witness_pairs,
            parity_group_size=size,
            sign_bit=base.protocol.sign_bit,
        )
        if protocol.parity_group_size > protocol.copies_per_bit:
            continue
        variant = replace(base, protocol=protocol)
        result = run_evaluation(variant, trials_per_attack, keys)
        pauli = result.matrix("pauli_measurement")
        rows.append(
            {
                "parity_group_size": size,
                "trials": len(result.trials),
                "parity_group_count": protocol.parity_group_count,
                "statistical_detection_rate": result.matrix("statistical").detection_rate,
                "pauli_detection_rate": pauli.detection_rate,
                "statistical_false_alarm_rate": result.matrix(
                    "statistical"
                ).false_alarm_rate,
                "pauli_false_alarm_rate": pauli.false_alarm_rate,
                "mean_mismatch_rate": mean(t.mismatch_rate for t in result.trials),
                "mean_runtime_seconds": mean(t.elapsed_seconds for t in result.trials),
                "mean_mismatch_rate_legitimate": mean(
                    t.mismatch_rate for t in result.trials if not t.is_attack
                ),
                "mean_mismatch_rate_attack": mean(
                    t.mismatch_rate for t in result.trials if t.is_attack
                ),
            }
        )
    return rows
