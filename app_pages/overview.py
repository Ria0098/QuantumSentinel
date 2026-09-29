"""Overview page: pre-generated results bundle as a dashboard."""

from __future__ import annotations

import streamlit as st

from ui.components import (
    callout,
    detector_rate_chart,
    empty_state,
    hero_header,
    kpi,
    prepare_theme,
    rate_line_chart,
    section_card,
    styled_table,
)
from web_helpers import (
    comparison_frame,
    detection_rate_frame,
    group_sweep_frame,
    load_bundle,
    noise_sweep_frame,
    per_attack_frame,
    scenario_overview_frame,
)

bundle = load_bundle()

evaluation = bundle.get("evaluation")
config = bundle.get("config") or {}

if evaluation is None:
    prepare_theme()
    hero_header(
        "Missing results bundle",
        "Run `scripts/generate_report.py` to produce `results/`.",
        badges=["Results required"],
        icon="inbox",
    )
    empty_state(
        "No evaluation data",
        "The overview reads `results/evaluation.json`. Generate the bundle from the repo root first.",
    )
    st.stop()

# --------------------------------------------------------------------------- hero
cfg_protocol = config.get("protocol", {})
parties = f"L={cfg_protocol.get('message_length', 8)}  n={cfg_protocol.get('copies_per_bit', 4)}  g={cfg_protocol.get('parity_group_size', 2)}"
seed = config.get("seed", 20260101)
hero_header(
    "Quantum threat detection",
    "Pre-generated results from the seed run in `results/`. "
    "Statistical detection 1.000, Pauli 0.600, false alarm 0.000 across 1,200 transactions.",
    badges=[f"seed {seed}", parties, "6 scenarios", "12 threshold rules"],
    icon="monitor_heart",
)

# --------------------------------------------------------------------------- KPIs
kcol = st.columns(4)
stat = evaluation["statistical"]
pauli = evaluation["pauli_measurement"]
with kcol[0]:
    kpi("Statistical detection", f"{stat['detection_rate']:.3f}",
        help="True positive rate across all five attack classes.",
        delta=f"{stat['true_positives']:,} / {stat['true_positives'] + stat['false_negatives']:,} attacks caught",
        status="safe", icon="monitor_heart")
with kcol[1]:
    kpi("Pauli detection", f"{pauli['detection_rate']:.3f}",
        help="Phase/bitwise detection rate. Blind to replay & unauthorised verification by design.",
        delta=f"{pauli['true_positives']:,} / {pauli['true_positives'] + pauli['false_negatives']:,} attacks caught",
        status="warning", icon="graphic_eq")
with kcol[2]:
    kpi("False alarm", f"{stat['false_alarm_rate']:.3f}",
        help="FRP on legitimate traffic; identical for both detectors (0.000).",
        delta="both detectors agree",
        status="info", icon="shield")
with kcol[3]:
    kpi("Throughput", f"{evaluation['mean_runtime_seconds'] * 1000:.0f} ms",
        help="Mean wall-clock time per transaction across 1,200 runs.",
        delta=f"{evaluation['total_trials']:,} transactions total",
        status="accent", icon="bolt")

# --------------------------------------------------------------------------- comparison
left, right = st.columns(2)
with left, section_card("Method comparison", "Confusion-matrix summary per detector — see docs/detection.md."):
    styled_table(
        comparison_frame(evaluation),
        badge_columns=["detector"],
    )
    callout(
        "The Pauli layer cannot see replay / unauthorised verification by design — only the classical rules do.",
        kind="info",
    )
with right, section_card("Per-attack results", "Detected counts and mean mismatch rate per attack class."):
    styled_table(
        per_attack_frame(evaluation),
        badge_columns=[],
        threat_on=["statistical detected", "pauli detected", "protocol rejected"],
    )

# --------------------------------------------------------------------------- bar chart
rate = detection_rate_frame(evaluation)
with section_card("Detection rate by attack", "Only attack classes shown; legitimate traffic is the false-alarm baseline"):
    if rate.empty:
        empty_state("No per-attack data", "Run the controlled evaluation to populate this chart.")
    else:
        chart = detector_rate_chart(rate).properties(height=310)
        st.altair_chart(chart, width="stretch", theme=None)

# --------------------------------------------------------------------------- sweeps
sweep_left, sweep_right = st.columns(2)
noise = bundle.get("noise_sweep")
with sweep_left, section_card("Decoherence robustness", "Detection rate vs per-qubit decoherence p"):
    if noise:
        noise_df = noise_sweep_frame(noise.get("decoherence_rates", []))
        if not noise_df.empty:
            chart = rate_line_chart(
                noise_df, x="rate:Q", x_title="decoherence rate p",
                title="Detection rate vs decoherence",
                threshold=0.02,
            ).properties(height=250)
            st.altair_chart(chart, width="stretch", theme=None)
            callout(
                "No false alarms up to p=0.02; the statistical layer collapses only at p=0.05.",
                kind="warning",
            )
    else:
        empty_state("No sweep data", "results/noise_sweep.json is missing.")

group = bundle.get("group_sweep")
with sweep_right, section_card("Group-size distillation", "Detection rate vs number of parity groups g"):
    if group:
        group_df = group_sweep_frame(group.get("parity_group_sizes", []))
        if not group_df.empty:
            chart = rate_line_chart(
                group_df, x="group size:Q", x_title="parity group size g",
                title="Detection rate vs group size",
            ).properties(height=250)
            st.altair_chart(chart, width="stretch", theme=None)
            callout(
                "Larger groups buy the same 1.000 detection with ~1/g the measurements.",
                kind="safe",
            )
    else:
        empty_state("No sweep data", "results/group_sweep.json is missing.")

# --------------------------------------------------------------------------- scenarios
scenarios = bundle.get("scenarios")
if scenarios:
    with section_card("Scenario verdicts", "One-run outcomes for every attack class in the bundle."):
        styled_table(
            scenario_overview_frame(scenarios),
            badge_columns=["ground truth", "statistical", "pauli", "protocol"],
        )