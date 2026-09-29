"""Evaluation page: run the controlled experiment live with chosen parameters."""

from __future__ import annotations

import streamlit as st

from ui.components import (
    callout,
    detector_rate_chart,
    empty_state,
    kpi_row,
    page_header,
    prepare_theme,
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

prepare_theme()

page_header(
    "Controlled evaluation",
    "Re-run the experiment the report describes with your own trials per attack and seed. "
    "Every verdict comes from the live engine, not the pre-generated bundle.",
    icon="analytics",
    chips=[("Live engine", "safe"), ("downloadable", "info")],
    meta=[f"{6} scenarios"],
)

with st.form("evaluation_form"):
    preset_col, trials_col, seed_col = st.columns(3, gap="medium")
    with preset_col:
        preset = st.selectbox("Channel preset", ["clean", "noisy", "degraded"], index=0)
    with trials_col:
        trials = st.number_input("Trials per attack", min_value=5, max_value=500, value=50, step=5)
    with seed_col:
        seed = st.number_input("Seed", min_value=1, max_value=2**31, value=20260101, step=1)
    submitted = st.form_submit_button("Run evaluation", type="primary")

if not submitted:
    empty_state(
        "Press run evaluation",
        "6 scenarios × N trials will run live against the real engine. "
        "Expect roughly 10 ms per transaction.",
        icon="timelapse",
    )
    st.stop()

with st.spinner(f"Running 6 scenarios x {int(trials)} trials..."):
    summary = run_evaluation_summary(preset, int(trials), int(seed))

stat = summary["statistical"]
pauli = summary["pauli_measurement"]
total = summary["total_trials"]

kpi_row(
    [
        {
            "label": "Statistical detection",
            "value": f"{stat['detection_rate']:.3f}",
            "help": "True positive rate across all five attack classes.",
            "delta": f"{stat['true_positives']:,} of "
                     f"{stat['true_positives'] + stat['false_negatives']:,} attacks caught",
            "delta_color": "normal",
            "icon": ":material/monitor_heart:",
        },
        {
            "label": "Pauli detection",
            "value": f"{pauli['detection_rate']:.3f}",
            "help": "Phase and bitwise detection rate. Blind to replay and unauthorised "
                    "verification by design.",
            "delta": f"{pauli['true_positives']:,} of "
                     f"{pauli['true_positives'] + pauli['false_negatives']:,} attacks caught",
            "delta_color": "off",
            "icon": ":material/graphic_eq:",
        },
        {
            "label": "False alarm",
            "value": f"{stat['false_alarm_rate']:.3f}",
            "help": "False-positive rate on legitimate traffic.",
            "delta": "both detectors agree",
            "delta_color": "off",
            "icon": ":material/shield:",
        },
        {
            "label": "Mean latency",
            "value": f"{summary['mean_runtime_seconds'] * 1000:.0f} ms",
            "help": "Mean wall-clock time per transaction for this run.",
            "delta": f"{total:,} txns in {summary['total_runtime_seconds']:.1f}s",
            "delta_color": "off",
            "icon": ":material/bolt:",
        },
    ]
)

left, right = st.columns(2, gap="medium")

with left, section_card(
    "Method comparison", "Confusion-matrix summary per detector.", icon="balance"
):
    styled_table(
        comparison_frame(summary),
        help={"detector": "The two independent detection layers."},
    )
    callout(
        "The Pauli layer cannot see replay or unauthorised verification by design — "
        "only the classical protocol rules do.",
        kind="info",
    )

with right, section_card(
    "Per-attack results",
    "Detected counts and mean mismatch rate per attack class.",
    icon="table_rows",
):
    styled_table(
        per_attack_frame(summary),
        help={
            "statistical detected": "Transactions flagged by the statistical layer.",
            "pauli detected": "Transactions flagged by the Pauli layer. Expected to be "
                              "0 for replay and unauthorised verification.",
            "protocol rejected": "Transactions the classical protocol refused.",
        },
    )

rate = detection_rate_frame(summary)
with section_card(
    "Detection rate by attack",
    "One bar per detection layer, per attack class.",
    icon="bar_chart",
):
    if rate.empty:
        empty_state("No per-attack data", "No attack rows were recorded.")
    else:
        st.altair_chart(
            detector_rate_chart(rate),
            width="stretch",
            theme=None,
        )

with section_card(
    "Export", "Download this run for the record or the report.", icon="download"
):
    dl_json, dl_csv = st.columns(2, gap="medium")
    with dl_json:
        st.download_button(
            "Download JSON",
            data=summary_json(summary),
            file_name=f"qsg_eval_{preset}_{int(seed)}.json",
            mime="application/json",
            width="stretch",
        )
    with dl_csv:
        st.download_button(
            "Download per-attack CSV",
            data=per_attack_csv(summary),
            file_name=f"qsg_eval_{preset}_{int(seed)}_per_attack.csv",
            mime="text/csv",
            width="stretch",
        )
