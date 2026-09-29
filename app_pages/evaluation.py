"""Evaluation page: run the controlled experiment live with chosen parameters."""

from __future__ import annotations

import streamlit as st

from ui.components import (
    callout,
    detector_rate_chart,
    empty_state,
    hero_header,
    kpi,
    section_card,
    styled_table,
)
from web_helpers import (
    comparison_frame,
    detection_rate_frame,
    per_attack_csv,
    per_attack_frame,
    run_evaluation_summary,
    summary_json,
)

hero_header(
    "Controlled evaluation",
    "Run the same experiment the report describes with your own trials per attack "
    "and seed. Every verdict comes from the live engine, not the pre-generated bundle.",
    badges=["Live engine", "6 scenarios", "downloadable results"],
    icon="analytics",
)

with st.form("evaluation_form"):
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        preset = st.selectbox("Channel preset", ["clean", "noisy", "degraded"], index=0)
    with col_b:
        trials = st.number_input("Trials per attack", min_value=5, max_value=500, value=50, step=5)
    with col_c:
        seed = st.number_input("Seed", min_value=1, max_value=2**31, value=20260101, step=1)
    submitted = st.form_submit_button("Run evaluation", type="primary")

if not submitted:
    empty_state(
        "Press Run evaluation",
        "6 scenarios × N trials will run live. Expect ~10 ms per transaction.",
        icon="timelapse",
    )
    st.stop()

with st.spinner(f"Running 6 scenarios x {trials} trials..."):
    summary = run_evaluation_summary(preset, int(trials), int(seed))

running = summary["total_trials"]
stat = summary["statistical"]
pauli = summary["pauli_measurement"]

# --------------------------------------------------------------------------- KPIs
st.caption(
    f"{running:,} transactions ({running / 6:,.0f} per attack) in "
    f"{summary['total_runtime_seconds']:.1f}s ≈ {summary['mean_runtime_seconds'] * 1000:.0f} ms/txn."
)
kcol = st.columns(4)
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
        help="FRP on legitimate traffic; identical for both detectors.",
        delta="both detectors agree",
        status="info", icon="shield")
with kcol[3]:
    kpi("Throughput", f"{summary['mean_runtime_seconds'] * 1000:.0f} ms",
        help="Mean wall-clock time per transaction for this run.",
        delta=f"{summary['total_runtime_seconds']:.1f}s total",
        status="accent", icon="bolt")

# --------------------------------------------------------------------------- comparison
left, right = st.columns(2)
with left, section_card("Method comparison", "Confusion-matrix summary per detector"):
    styled_table(comparison_frame(summary), badge_columns=["detector"])
    callout(
        "The Pauli layer cannot see replay / unauthorised verification by design — only the classical rules do.",
        kind="info",
    )
with right, section_card("Per-attack results", "Detected counts and mean mismatch rate per attack class"):
    styled_table(
        per_attack_frame(summary),
        threat_on=["statistical detected", "pauli detected", "protocol rejected"],
    )

# --------------------------------------------------------------------------- chart
rate = detection_rate_frame(summary)
with section_card("Detection rate by attack", "Only attack classes shown; legitimate traffic is the false-alarm baseline"):
    if rate.empty:
        empty_state("No per-attack data", "No attack rows were recorded.")
    else:
        chart = detector_rate_chart(rate).properties(height=300)
        st.altair_chart(chart, width="stretch", theme=None)

# --------------------------------------------------------------------------- downloads
with section_card("Export", "Download this run as JSON or CSV for the record / report."):
    dl_a, dl_b = st.columns(2)
    with dl_a:
        st.download_button(
            "Download JSON",
            data=summary_json(summary),
            file_name=f"qsg_eval_{preset}_{int(seed)}.json",
            mime="application/json",
            key="dl_json",
        )
    with dl_b:
        st.download_button(
            "Download per-attack CSV",
            data=per_attack_csv(summary),
            file_name=f"qsg_eval_{preset}_{int(seed)}_per_attack.csv",
            mime="text/csv",
            key="dl_csv",
        )