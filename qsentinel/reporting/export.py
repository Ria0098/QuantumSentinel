"""Export of scenario and evaluation results to JSON and Markdown."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..session import ScenarioResult
from .console import heading, table


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write ``payload`` to ``path`` as pretty JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def scenario_as_dict(result: ScenarioResult) -> dict[str, Any]:
    computed = result.detection.measures()
    return {
        "scenario": result.attack,
        "title": result.title,
        "is_attack": result.is_attack,
        "notes": result.notes,
        "expected_quantum_visible": result.expected_quantum_visible,
        "accepted_by_protocol": result.accepted_by_protocol,
        "elapsed_seconds": result.elapsed_seconds,
        "comparison": {
            "statistical": result.detection.statistical.is_threat,
            "pauli_measurement": result.detection.pauli.is_threat,
            "agree": result.detection.agree,
        },
        "verification": {
            "signature_valid": result.verification.signature_valid,
            "freshness_ok": result.verification.freshness_ok,
            "authorisation_ok": result.verification.authorisation_ok,
            "reject_reason": result.verification.reject_reason,
            "mismatch_count": result.verification.mismatch_count(),
            "check_count": len(result.verification.all_checks()),
            "mismatch_rate": float(result.verification.mismatch_rate()),
            "failing_checks": [
                {
                    "label": check.label,
                    "kind": check.kind,
                    "expected": check.expected,
                    "observed": check.observed,
                    "detail": check.detail,
                }
                for check in result.verification.all_checks()
                if not check.passed
            ],
        },
        "detection_measures": {
            key: {
                "name": measure.name,
                "value": measure.value,
                "threshold": measure.threshold,
                "comparison": measure.comparison,
                "tripped": measure.tripped,
            }
            for key, measure in computed.items()
        },
    }


def scenario_to_markdown(result: ScenarioResult) -> str:
    """Render a scenario result as a self-contained Markdown section."""
    verification = result.verification
    detection = result.detection
    lines = [
        f"## Scenario: {result.title} (`{result.attack}`)\n",
        f"- Adversarial action: {result.notes}",
        f"- Ground truth: {'ATTACK' if result.is_attack else 'benign'} "
        f"| quantum-visible in measurement data: {result.expected_quantum_visible}",
        f"- Protocol decision: {'REJECT' if not result.accepted_by_protocol else 'ACCEPT'}",
        f"- Runtime: {result.elapsed_seconds * 1000:.2f} ms",
        "",
        "### Verification",
        "",
        f"- Signature valid: {verification.signature_valid}",
        f"- Freshness: {verification.freshness_ok}",
        f"- Authorisation: {verification.authorisation_ok}",
        f"- Reject reason: {verification.reject_reason or 'none'}",
        f"- Mismatch rate E = {float(verification.mismatch_rate()):.4f} "
        f"({verification.mismatch_count()}/{len(verification.all_checks())})",
        "",
    ]
    for unique in "statistical pauli_measurement".split():
        detector = getattr(detection, "statistical" if unique == "statistical" else "pauli")
        lines.append(f"### Method {1 if unique == 'statistical' else 2}: {unique}")
        lines.append("")
        lines.append(
            table(
                ["signal", "value", "rule", "threshold", "tripped"],
                [
                    [
                        measure.name,
                        f"{measure.value:.4f}",
                        measure.comparison,
                        f"{measure.threshold:.4f}",
                        "yes" if measure.tripped else "no",
                    ]
                    for measure in detector.signals
                ],
                ["left", "right", "center", "right", "left"],
            )
        )
        lines.append("")
    return "\n".join(lines)