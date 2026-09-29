"""Shared helpers for the QuantumSigGuard dashboard pages.

All pure "view" logic: loads the pre-generated ``results/`` bundle, runs the
same ``qsentinel`` engine the CLI uses, and reshapes results into DataFrames
for Streamlit.  Nothing here replaces or duplicates engine logic.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import pandas as pd

from qsentinel.attacks import ATTACK_ORDER, describe_attacks
from qsentinel.config import PRESETS
from qsentinel.evaluation import run_evaluation, run_group_size_sweep, run_noise_sweep
from qsentinel.session import QDSSession

REPO = Path(__file__).resolve().parent
RESULTS = REPO / "results"

PRESET_NAMES = list(PRESETS)

DETECTOR_LABELS = {
    "statistical": "statistical",
    "pauli_measurement": "pauli measurement",
}


# ---------------------------------------------------------------- results bundle

def _load_json(name: str) -> Any:
    path = RESULTS / f"{name}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_bundle() -> dict[str, Any]:
    """Read the pre-generated ``results/`` artifacts (or ``None`` when absent)."""
    return {
        "config": _load_json("config"),
        "scenarios": _load_json("scenarios"),
        "evaluation": _load_json("evaluation"),
        "noise_sweep": _load_json("noise_sweep"),
        "group_sweep": _load_json("group_sweep"),
    }


# ------------------------------------------------------------ engine front-ends

def run_scenario_result(preset: str, attack: str, seed: int) -> dict[str, Any]:
    """Run one scenario and return :meth:`ScenarioResult.as_dict`.

    Mirrors ``generate_report.py``: a benign transaction is run first so the
    replay attack has an accepted transaction to replay.
    """
    base = PRESETS[preset].seeded(seed)
    session = QDSSession(base)
    if attack == "replay":
        session.run_scenario("legitimate")
    result = session.run_scenario(attack)
    return result.as_dict()


def run_evaluation_summary(
    preset: str, trials_per_attack: int, seed: int
) -> dict[str, Any]:
    """Run the full evaluation (`run_evaluation(...).summary()`)."""
    base = PRESETS[preset].seeded(seed)
    result = run_evaluation(base, trials_per_attack=trials_per_attack)
    return result.summary()


def run_noise_sweep_rows(preset: str, trials_per_attack: int, seed: int) -> list[dict]:
    """Sweep decoherence and return the row list from `run_noise_sweep`."""
    base = PRESETS[preset].seeded(seed)
    rates = (0.000, 0.002, 0.005, 0.010, 0.020, 0.050)
    return run_noise_sweep(rates, base, trials_per_attack=trials_per_attack)


def run_group_sweep_rows(preset: str, trials_per_attack: int, seed: int) -> list[dict]:
    """Sweep the parity group size and return the row list."""
    base = PRESETS[preset].seeded(seed)
    sizes = (1, 2, 3, 4)
    return run_group_size_sweep(sizes, base, trials_per_attack=trials_per_attack)


# -------------------------------------------------------------------- reshaping

def scenario_options() -> list[str]:
    """Attack keys in canonical order for a selectbox."""
    return list(ATTACK_ORDER)


def signals_frame(result: dict[str, Any], detector: str) -> pd.DataFrame:
    """Table of one detector's signals: value, rule, threshold, state."""
    rows = []
    for signal in result["detection"][detector]["signals"]:
        rows.append(
            {
                "signal": signal["name"],
                "value": round(signal["value"], 4),
                "threshold": round(signal["threshold"], 4),
                "rule": signal["comparison"],
                "tripped": "yes" if signal["tripped"] else "no",
            }
        )
    return pd.DataFrame(rows, columns=["signal", "value", "threshold", "rule", "tripped"])


def checks_frame(result: dict[str, Any]) -> pd.DataFrame:
    """Table of the protocol verification checks that failed."""
    rows = []
    for check in result["verification"]["checks"]:
        if check["passed"]:
            continue
        rows.append(
            {
                "kind": check["kind"],
                "label": check["label"],
                "expected": check["expected"],
                "observed": check["observed"],
                "detail": check["detail"],
            }
        )
    return pd.DataFrame(rows, columns=["kind", "label", "expected", "observed", "detail"])


def comparison_frame(summary: dict[str, Any]) -> pd.DataFrame:
    """Per-detector confusion-matrix summary."""
    rows = []
    for key in ("statistical", "pauli_measurement"):
        metrics = summary[key]
        lower, upper = metrics["detection_rate_ci95"]
        rows.append(
            {
                "detector": DETECTOR_LABELS[key],
                "detection rate": round(metrics["detection_rate"], 4),
                "95% CI": f"{lower:.4f}–{upper:.4f}",
                "false alarm": round(metrics["false_alarm_rate"], 4),
                "accuracy": round(metrics["accuracy"], 4),
            }
        )
    return pd.DataFrame(rows, columns=["detector", "detection rate", "95% CI", "false alarm", "accuracy"])


def per_attack_frame(summary: dict[str, Any]) -> pd.DataFrame:
    """Per-attack detected counts for both detectors."""
    rows = []
    for row in summary["per_attack"]:
        rows.append(
            {
                "attack": row["attack"],
                "trials": row["trials"],
                "statistical detected": row["statistical_detected"],
                "pauli detected": row["pauli_detected"],
                "protocol rejected": row["protocol_rejected"],
                "mean mismatch E": round(row["mean_mismatch_rate"], 4),
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "attack",
            "trials",
            "statistical detected",
            "pauli detected",
            "protocol rejected",
            "mean mismatch E",
        ],
    )


def detection_rate_frame(summary: dict[str, Any]) -> pd.DataFrame:
    """Per-attack detection rate per detector (legitimate row excluded)."""
    rows = []
    for row in summary["per_attack"]:
        if not row["is_attack"]:
            continue
        rows.append(
            {
                "attack": row["attack"],
                "detector": "statistical",
                "detection rate": row["statistical_detected"] / row["trials"],
            }
        )
        rows.append(
            {
                "attack": row["attack"],
                "detector": "pauli",
                "detection rate": row["pauli_detected"] / row["trials"],
            }
        )
    return pd.DataFrame(rows, columns=["attack", "detector", "detection rate"])


def noise_sweep_frame(rows: list[dict]) -> pd.DataFrame:
    """Long-format detection-rate series vs decoherence rate."""
    entries = []
    for row in rows:
        base = {"rate": row["decoherence_rate"]}
        entries.append({**base, "detector": "statistical", "detection rate": row["statistical_detection_rate"]})
        entries.append({**base, "detector": "pauli", "detection rate": row["pauli_detection_rate"]})
    return pd.DataFrame(entries, columns=["rate", "detector", "detection rate"])


def group_sweep_frame(rows: list[dict]) -> pd.DataFrame:
    """Long-format detection-rate series vs parity group size."""
    entries = []
    for row in rows:
        base = {"group size": row["parity_group_size"]}
        entries.append({**base, "detector": "statistical", "detection rate": row["statistical_detection_rate"]})
        entries.append({**base, "detector": "pauli", "detection rate": row["pauli_detection_rate"]})
    return pd.DataFrame(entries, columns=["group size", "detector", "detection rate"])


def scenario_overview_frame(scenarios: list[dict]) -> pd.DataFrame:
    """Compact table of every scenario verdict pair."""
    rows = []
    for entry in scenarios:
        verdict = entry["comparison"]
        rows.append(
            {
                "scenario": entry["title"],
                "ground truth": "ATTACK" if entry["is_attack"] else "benign",
                "statistical": "THREAT" if verdict["statistical"] else "LEGITIMATE",
                "pauli": "THREAT" if verdict["pauli_measurement"] else "LEGITIMATE",
                "protocol": "REJECT" if not entry["accepted_by_protocol"] else "ACCEPT",
            }
        )
    return pd.DataFrame(rows, columns=["scenario", "ground truth", "statistical", "pauli", "protocol"])


# ----------------------------------------------------------------- presentation-only
# Helpers below are pure formatting/export shims used by the UI pages.  They
# add no engine behaviour and only reshape data the engine already produced.

PAULI_BLIND_ATTACKS = {"replay", "unauthorized_verification"}


def attack_descriptions() -> dict[str, str]:
    """Plain-English one-liners per attack, from the engine metadata."""
    return {key: meta["description"] for key, meta in describe_attacks().items()}


def scenario_description(attack: str) -> str:
    """One-liner describing the selected attack scenario."""
    meta = describe_attacks().get(attack) or {}
    return meta.get("description", "Unknown scenario.")


def pauli_explainer(attack: str) -> str | None:
    """Explain why Pauli reports LEGITIMATE when the classical stack caught the attack."""
    if attack in PAULI_BLIND_ATTACKS:
        name = describe_attacks().get(attack, {}).get("title", attack)
        return (
            f"'{name}' leaves the shared quantum state untouched — phase interference "
            "and bitwise checks cannot see it. Only the classical protocol layer "
            "(authentication, replay window, authorisation) can reject it."
        )
    return None


def summary_json(summary: dict[str, Any]) -> str:
    """Pretty-printed JSON payload for the evaluation download button."""
    return json.dumps(summary, indent=2, ensure_ascii=False)


def per_attack_csv(summary: dict[str, Any]) -> str:
    """CSV of the per-attack confusion counts for the evaluation download button."""
    return per_attack_frame(summary).to_csv(index=False)


def scenario_csv(scenarios: list[dict]) -> str:
    """CSV of the compact scenario verdict table."""
    return scenario_overview_frame(scenarios).to_csv(index=False)


def bundle_csv(bundle: dict[str, Any]) -> str:
    """Single CSV combining the evaluation comparison and per-attack tables."""
    buffer = io.StringIO()
    evaluation = bundle.get("evaluation") or {}
    if evaluation:
        comparison_frame(evaluation).to_csv(buffer, index=False)
        buffer.write("\n")
        per_attack_frame(evaluation).to_csv(buffer, index=False)
    return buffer.getvalue()