"""Overview page: the pre-generated ``results/`` bundle as a dashboard."""

from __future__ import annotations

import streamlit as st

from ui.components import (
    callout,
    detector_rate_chart,
    empty_state,
    kpi,
    kpi_row,
    page_header,
    pipeline,
    prepare_theme,
    rate_line_chart,
    section_card,
    styled_table,
)
from web_helpers import (
    comparison_frame,
    detection_rate_frame,
    group_sweep_frame,
    group_summary,
    load_bundle,
    noise_sweep_frame,
    noise_summary,
    per_attack_frame,
    scenario_overview_frame,
)

prepare_theme()

bundle = load_bundle()
evaluation = bundle.get("evaluation")
config = bundle.get("config") or {}

if evaluation is None:
    page_header(
        "Missing results bundle",
        "The overview reads the pre-generated `results/` artifacts.",
        icon="inbox",
        chips=["Results required"],
    )
    empty_state(
        "No evaluation data",
        "Run `python3 scripts/generate_report.py` from the repo root to produce `results/`, "
        "then reload this page.",
    )
    st.stop()

# --------------------------------------------------------------------------- header

protocol = config.get("protocol", {})
stat = evaluation["statistical"]
pauli = evaluation["pauli_measurement"]
total_txn = evaluation["total_trials"]
scenarios = bundle.get("scenarios")
scenario_count = len(scenarios) if scenarios else 6

page_header(
    "Quantum threat detection",
    f"Statistical detection {stat['detection_rate']:.3f}, Pauli "
    f"{pauli['detection_rate']:.3f}, false alarm {stat['false_alarm_rate']:.3f} "
    f"across {total_txn:,} transactions.",
    icon="monitor_heart",
    chips=[("Seeded report", "info")],
    meta=[
        "seed " + str(config.get("seed", 20260101)),
        f"L={protocol.get('message_length', 8)}",
        f"n={protocol.get('copies_per_bit', 4)}",
        f"g={protocol.get('parity_group_size', 2)}",
        f"{scenario_count} scenarios",
    ],
)

pipeline(
    [
        ("Sign", "X/Z eigenstates", "draw"),
        ("Teleport", "Bell pairs", "swap_horiz"),
        ("Channel", "noise + attack", "compare_arrows"),
        ("Verify", "Pauli correction", "fact_check"),
        ("Detect", "2-layer rule set", "monitor_heart"),
    ],
    title="Transaction flow",
)

# --------------------------------------------------------------------------- KPIs

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
                    "verification by design — only the classical layer catches those.",
            "delta": f"{pauli['true_positives']:,} of "
                     f"{pauli['true_positives'] + pauli['false_negatives']:,} attacks caught",
            "delta_color": "off",
            "icon": ":material/graphic_eq:",
        },
        {
            "label": "False alarm",
            "value": f"{stat['false_alarm_rate']:.3f}",
            "help": "False-positive rate on legitimate traffic. Identical for both detectors.",
            "delta": "both detectors agree",
            "delta_color": "off",
            "icon": ":material/shield:",
        },
        {
            "label": "Mean latency",
            "value": f"{evaluation['mean_runtime_seconds'] * 1000:.0f} ms",
            "help": "Mean wall-clock time per transaction.",
            "delta": f"{total_txn:,} transactions",
            "delta_color": "off",
            "icon": ":material/bolt:",
        },
    ]
)

# --------------------------------------------------------------------------- tables

left, right = st.columns(2, gap="medium")

with left, section_card(
    "Method comparison", "Confusion-matrix summary per detector.", icon="balance"
):
    styled_table(
        comparison_frame(evaluation),
        help={"detector": "The two independent detection layers."},
    )
    callout(
        "The Pauli layer cannot see replay or unauthorised verification by design — "
        "only the classical protocol rules do.",
        kind="info",
    )

with right, section_card(
    "Per-attack results",
    "Detected counts and mean mismatch rate per attack class. Legitimate traffic "
    "should show zeros everywhere.",
    icon="table_rows",
):
    styled_table(
        per_attack_frame(evaluation),
        help={
            "statistical detected": "Transactions flagged by the statistical layer.",
            "pauli detected": "Transactions flagged by the Pauli layer. Expected to be "
                              "0 for replay and unauthorised verification.",
            "protocol rejected": "Transactions the classical protocol refused.",
        },
    )

# --------------------------------------------------------------------------- charts

rate = detection_rate_frame(evaluation)
with section_card(
    "Detection rate by attack",
    "One bar per detection layer, per attack class.",
    icon="bar_chart",
):
    if rate.empty:
        empty_state("No per-attack data", "Run the controlled evaluation to populate this chart.")
    else:
        st.altair_chart(
            detector_rate_chart(rate),
            width="stretch",
            theme=None,
        )

# --------------------------------------------------------------------------- sweeps

sweep_left, sweep_right = st.columns(2, gap="medium")

noise = bundle.get("noise_sweep")
with sweep_left, section_card(
    "Decoherence robustness",
    "Detection rate against per-qubit decoherence.",
    icon="blur_on",
):
    if noise:
        noise_df = noise_sweep_frame(noise.get("decoherence_rates", []))
        if not noise_df.empty:
            st.altair_chart(
                rate_line_chart(
                    noise_df,
                    x="rate:Q",
                    x_title="decoherence rate p",
                    title="",
                    threshold=0.02,
                ).properties(height=260),
                width="stretch",
                theme=None,
            )
            callout(noise_summary(noise["decoherence_rates"]), kind="warning")
    else:
        empty_state("No sweep data", "`results/noise_sweep.json` is missing.")

group = bundle.get("group_sweep")
with sweep_right, section_card(
    "Group-size distillation",
    "Detection rate against the number of parity groups.",
    icon="grid_view",
):
    if group:
        group_df = group_sweep_frame(group.get("parity_group_sizes", []))
        if not group_df.empty:
            st.altair_chart(
                rate_line_chart(
                    group_df,
                    x="group size:Q",
                    x_title="parity group size g",
                    title="",
                ).properties(height=260),
                width="stretch",
                theme=None,
            )
            callout(group_summary(group["parity_group_sizes"]), kind="safe")
    else:
        empty_state("No sweep data", "`results/group_sweep.json` is missing.")

# --------------------------------------------------------------------------- scenarios

if scenarios:
    with section_card(
        "Scenario verdicts",
        "One run of every scenario, showing what each layer decided.",
        icon="checklist",
    ):
        styled_table(
            scenario_overview_frame(scenarios),
            help={
                "ground truth": "Whether the scenario is an attack or a legitimate transaction.",
                "statistical": "Statistical layer verdict.",
                "pauli": "Pauli layer verdict.",
                "protocol": "Classical protocol outcome.",
            },
        )
