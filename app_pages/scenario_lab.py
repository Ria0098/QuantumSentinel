"""Scenario lab: run one transaction and inspect both detection layers."""

from __future__ import annotations

import streamlit as st

from ui.components import (
    badge,
    callout,
    empty_state,
    kpi_row,
    page_header,
    prepare_theme,
    section_card,
    signal_dataframe,
    styled_table,
)
from web_helpers import (
    checks_frame,
    pauli_explainer,
    run_scenario_result,
    scenario_description,
    scenario_options,
)

prepare_theme()

ATTACK_TITLES = {
    "legitimate": "Legitimate transaction",
    "forgery": "Signature forgery",
    "impersonation": "Sender impersonation",
    "replay": "Replay attack",
    "unauthorized_verification": "Unauthorised verification",
    "channel_manipulation": "Quantum channel manipulation",
}

page_header(
    "Scenario lab",
    "Run one scenario end to end — sign, distribute through the channel, verify — "
    "then inspect every signal both detection layers produced.",
    icon="science",
    chips=[
        ("Live engine", "safe"),
        ("SEEDED", "info"),
        ("replay auto-seeds history", "neutral"),
    ],
)

with st.form("scenario_form"):
    preset_col, attack_col, seed_col = st.columns([1, 2, 1], gap="medium")
    with preset_col:
        preset = st.selectbox("Channel preset", ["clean", "noisy", "degraded"], index=0)
    with attack_col:
        attack = st.selectbox(
            "Scenario",
            scenario_options(),
            format_func=lambda key: ATTACK_TITLES.get(key, key),
        )
    with seed_col:
        seed = st.number_input("Seed", min_value=1, max_value=2**31, value=20260101, step=1)
    submitted = st.form_submit_button("Run scenario", type="primary")

st.caption(scenario_description(attack))

if not submitted:
    empty_state(
        "Press run scenario",
        "The verdict strip, both signal tables and any failed protocol checks will appear here.",
        icon="play_circle",
    )
    st.stop()

result = run_scenario_result(preset, attack, seed=int(seed))

detection = result["detection"]
stat_threat = detection["statistical"]["is_threat"]
pauli_threat = detection["pauli_measurement"]["is_threat"]
protocol_rejected = not result["accepted_by_protocol"]
verification = result["verification"]

# --------------------------------------------------------------------------- verdicts

kpi_row(
    [
        {
            "label": "Protocol",
            "value": "REJECT" if protocol_rejected else "ACCEPT",
            "help": "Classical rules: signature validity, freshness, authorisation, mismatch rate.",
            "delta": f"mismatch rate {verification['mismatch_rate']:.4f}",
            "delta_color": "inverse" if protocol_rejected else "normal",
            "icon": ":material/verified_user:",
        },
        {
            "label": "Statistical layer",
            "value": "THREAT" if stat_threat else "LEGITIMATE",
            "help": "Mismatch, QBER, per-basis QBER and distribution-distance signals.",
            "delta": "flagged" if stat_threat else "clear",
            "delta_color": "inverse" if stat_threat else "normal",
            "icon": ":material/monitor_heart:",
        },
        {
            "label": "Pauli layer",
            "value": "THREAT" if pauli_threat else "LEGITIMATE",
            "help": "Correlator agreement and retained-witness parity signals.",
            "delta": "flagged" if pauli_threat else "clear",
            "delta_color": "inverse" if pauli_threat else "normal",
            "icon": ":material/graphic_eq:",
        },
        {
            "label": "Latency",
            "value": f"{result['elapsed_seconds'] * 1000:.2f} ms",
            "help": "Wall-clock time for this single run.",
            "delta": f"seed {int(seed)}",
            "delta_color": "off",
            "icon": ":material/bolt:",
        },
    ]
)

# --------------------------------------------------------------------------- protocol checks

with section_card(
    "Classical protocol verdict",
    "Independent of the two quantum detectors — these rules alone can stop replay and "
    "unauthorised verification.",
    icon="verified_user",
):
    with st.container(horizontal=True, gap="small"):
        badge("ACCEPT" if verification["signature_valid"] else "FAIL")
        st.caption("signature")
        badge("ACCEPT" if verification["freshness_ok"] else "FAIL")
        st.caption("freshness")
        badge("ACCEPT" if verification["authorisation_ok"] else "FAIL")
        st.caption("authorisation")

    if verification["reject_reason"]:
        callout(f"Reject reason: {verification['reject_reason']}", kind="threat")

# --------------------------------------------------------------------------- signals

stat_col, pauli_col = st.columns(2, gap="medium")

with stat_col, section_card(
    "Method 1 — statistical signals",
    "Each signal measured against its own threshold.",
    icon="monitor_heart",
):
    signal_dataframe(
        detection["statistical"]["signals"],
        empty_message="This detector produced no signal rows.",
    )

with pauli_col, section_card(
    "Method 2 — Pauli measurement signals",
    "Each signal measured against its own threshold.",
    icon="graphic_eq",
):
    signal_dataframe(
        detection["pauli_measurement"]["signals"],
        empty_message="This detector produced no signal rows.",
    )

# --------------------------------------------------------------------------- failed checks

failed = checks_frame(result)
with section_card(
    "Failed protocol checks",
    "Only the checks that did not pass.",
    icon="rule",
):
    if failed.empty:
        callout(
            "All protocol checks passed — the transaction is legitimate on every classical rule.",
            kind="safe",
        )
    else:
        styled_table(
            failed,
            help={
                "kind": "Which verification family the check belongs to.",
                "expected": "What the protocol required.",
                "observed": "What the verifier actually saw.",
            },
        )

explainer = pauli_explainer(attack)
if explainer and not pauli_threat and (stat_threat or protocol_rejected):
    callout(explainer, kind="info")
