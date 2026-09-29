"""Human-readable rendering of a scenario result."""

from __future__ import annotations

from typing import Any

from ..session import ScenarioResult
from .console import (
    bar,
    bold,
    colour,
    heading,
    rule,
    table,
    verdict_label,
)

_SEVERITY = {
    True: "threat",
    False: "legitimate",
}


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def render_scenario(result: ScenarioResult, verbose: bool = True) -> str:
    """Return the full console report for one scenario."""
    lines: list[str] = []
    verification = result.verification
    detection = result.detection

    lines.append(heading(f"Scenario: {result.title}  [{result.attack}]"))
    lines.append("")
    lines.append(f"  {colour('Adversarial action', 'accent')}: {result.notes}")
    lines.append(
        f"  {colour('Ground truth', 'accent')}: "
        f"{'ATTACK' if result.is_attack else 'no attack'}   "
        f"quantum-visible: {result.expected_quantum_visible}"
    )
    lines.append("")

    txn = verification.transaction
    lines.append(colour("  Protocol data", "info"))
    lines.append(
        f"    transaction {txn.transaction_id}  nonce {txn.nonce}  "
        f"message {txn.message}  length {txn.length}"
    )
    lines.append(
        f"    requester '{txn.requesting_entity}'  "
        f"authorised: {colour(str(txn.authorised), _SEVERITY[txn.authorised])}"
    )
    lines.append(
        f"    basis pattern {''.join(b[0] for b in txn.bases())}  "
        f"(key redacted; target eigenvalues "
        f"{''.join('+' if e == 1 else '-' for e in txn.expected_eigenvalues())})"
    )
    lines.append("")

    lines.append(colour("  Distribution", "info"))
    distributed = verification.distributed
    lines.append(
        f"    {len(distributed.test_qubits)} teleportation copies  "
        f"{len(distributed.witness_pairs)} witness pairs  "
        f"{distributed.dropped_qubits} dropped  "
        f"{distributed.tampered_messages()} classical messages tampered"
    )
    residual = distributed.residual_errors()
    lines.append(
        "    residual Pauli errors: "
        + ", ".join(f"{k}={v}" for k, v in sorted(residual.items()))
    )
    lines.append("")

    lines.append(colour("  Verification", "info"))
    lines.append(
        f"    signature valid: {verdict_label(not verification.signature_valid)}"
        f"    freshness: {verdict_label(not verification.freshness_ok)}"
        f"    authorisation: {verdict_label(not verification.authorisation_ok)}"
    )
    checks = verification.all_checks()
    by_kind: dict[str, list] = {}
    for check in checks:
        by_kind.setdefault(check.kind, []).append(check)
    lines.append(
        table(
            ["check family", "checks", "failed", "pass rate"],
            [
                [
                    kind,
                    len(items),
                    sum(1 for item in items if not item.passed),
                    _pct(1.0 - sum(1 for i in items if not i.passed) / len(items)),
                ]
                for kind, items in by_kind.items()
            ],
            ["left", "right", "right", "right"],
        )
    )
    lines.append(
        f"    overall mismatch rate E = {float(verification.mismatch_rate()):.4f} "
        f"({verification.mismatch_count()}/{len(checks)})"
    )
    if verification.reject_reason:
        lines.append(f"    reject reason: {colour(verification.reject_reason, 'warn')}")
    lines.append("")

    lines.append(colour("  Detection - Method 1: statistical", "accent"))
    stat = detection.statistical
    lines.append(f"    verdict: {verdict_label(stat.is_threat)}")
    lines.append(
        table(
            ["signal", "value", "rule", "threshold", "state"],
            [
                [
                    signal.name,
                    f"{signal.value:.4f}",
                    signal.comparison,
                    f"{signal.threshold:.4f}",
                    colour("TRIPPED", "threat") if signal.tripped else colour("ok", "legitimate"),
                ]
                for signal in stat.signals
            ],
            ["left", "right", "center", "right", "left"],
        )
    )
    lines.append("")

    lines.append(colour("  Detection - Method 2: Pauli measurement", "accent"))
    pauli = detection.pauli
    lines.append(f"    verdict: {verdict_label(pauli.is_threat)}")
    lines.append(
        table(
            ["signal", "value", "rule", "threshold", "state"],
            [
                [
                    signal.name,
                    f"{signal.value:+.4f}",
                    signal.comparison,
                    f"{signal.threshold:.4f}",
                    colour("TRIPPED", "threat") if signal.tripped else colour("ok", "legitimate"),
                ]
                for signal in pauli.signals
            ],
            ["left", "right", "center", "right", "left"],
        )
    )
    lines.append(
        f"    {colour('per-basis measurement summary', 'muted')}:"
    )
    lines.append(
        table(
            ["basis", "copies", "expected +1", "observed +1", "distance", "parity"],
            [
                [
                    basis,
                    int(entry["copies"]),
                    _pct(entry["expected_positive_fraction"]),
                    _pct(entry["observed_positive_fraction"]),
                    f"{entry['distribution_distance']:.4f}",
                    f"{entry['parity_agreement']:.3f}",
                ]
                for basis, entry in sorted(detection.measurement_summary.items())
            ],
            ["left", "right", "right", "right", "right", "right"],
        )
    )
    lines.append("")

    agreement = colour("agree", "legitimate") if detection.agree else colour("DISAGREE", "warn")
    lines.append(
        f"  {bold('Comparison')}: the two methods {agreement} on this transaction."
    )
    lines.append(
        f"  {bold('Protocol outcome')}: "
        f"{colour('REJECTED', 'threat') if not result.accepted_by_protocol else colour('ACCEPTED', 'legitimate')}"
        f"    runtime {result.elapsed_seconds * 1000:.2f} ms"
    )

    if verbose:
        failing = [check for check in checks if not check.passed]
        if failing:
            lines.append("")
            lines.append(colour("  Failing checks", "warn"))
            lines.append(
                table(
                    ["label", "kind", "expected", "observed", "detail"],
                    [
                        [
                            check.label,
                            check.kind,
                            check.expected,
                            check.observed,
                            check.detail,
                        ]
                        for check in failing[:12]
                    ],
                    ["left", "left", "right", "right", "left"],
                )
            )
            if len(failing) > 12:
                lines.append(colour(f"    ... and {len(failing) - 12} more", "muted"))
    return "\n".join(lines)


def render_comparison(results: list[ScenarioResult]) -> str:
    """Render a side-by-side comparison table for a set of scenarios."""
    rows = []
    for result in results:
        rows.append(
            [
                result.attack,
                "attack" if result.is_attack else "legit",
                verdict_label(result.detection.statistical.is_threat),
                verdict_label(result.detection.pauli.is_threat),
                colour("REJECT", "threat")
                if not result.accepted_by_protocol
                else colour("ACCEPT", "legitimate"),
                f"{float(result.verification.mismatch_rate()):.4f}",
            ]
        )
    header = rule()
    return "\n".join(
        [
            heading("Method comparison"),
            table(
                [
                    "scenario",
                    "truth",
                    "statistical",
                    "pauli",
                    "protocol",
                    "E",
                ],
                rows,
                ["left", "left", "left", "left", "left", "right"],
            ),
            header,
        ]
    )


def render_evaluation(summary: dict[str, Any]) -> str:
    """Render an evaluation summary produced by :mod:`qsentinel.evaluation`."""
    lines = [heading("Evaluation summary"), ""]
    lines.append(
        f"  trials: {summary['total_trials']}   "
        f"total runtime: {summary['total_runtime_seconds']:.2f} s   "
        f"mean per transaction: {summary['mean_runtime_seconds'] * 1000:.2f} ms"
    )
    lines.append("")
    rows = []
    for detector in ("statistical", "pauli_measurement"):
        entry = summary[detector]
        detection_ci = entry["detection_rate_ci95"]
        alarm_ci = entry["false_alarm_rate_ci95"]
        rows.append(
            [
                detector,
                f"{entry['detection_rate']:.3f} "
                f"[{detection_ci[0]:.3f},{detection_ci[1]:.3f}]",
                f"{entry['false_alarm_rate']:.3f} "
                f"[{alarm_ci[0]:.3f},{alarm_ci[1]:.3f}]",
                f"{entry['accuracy']:.3f}",
                f"{bar(entry['detection_rate'])}",
            ]
        )
    lines.append(
        table(
            ["detector", "detection rate (95% CI)", "false-alarm rate (95% CI)", "accuracy", ""],
            rows,
            ["left", "left", "left", "right", "left"],
        )
    )
    lines.append("")
    lines.append(colour("  Per-attack results", "accent"))
    lines.append(
        table(
            ["attack", "trials", "statistical", "pauli", "protocol rejected", "mean E"],
            [
                [
                    row["attack"],
                    row["trials"],
                    row["statistical_detected"],
                    row["pauli_detected"],
                    row["protocol_rejected"],
                    f"{row['mean_mismatch_rate']:.4f}",
                ]
                for row in summary["per_attack"]
            ],
            ["left", "right", "right", "right", "right", "right"],
        )
    )
    return "\n".join(lines)
