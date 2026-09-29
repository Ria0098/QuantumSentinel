"""Scenario lab: run a single transaction and inspect both detection layers."""

from __future__ import annotations

import streamlit as st

from ui.components import (
    callout,
    empty_state,
    hero_header,
    kpi,
    section_card,
    signal_progress,
    styled_table,
)
from web_helpers import (
    checks_frame,
    pauli_explainer,
    run_scenario_result,
    scenario_description,
    scenario_options,
    signals_frame,
)

ATTACK_TITLES = {
    "legitimate": "Legitimate transaction",
    "forgery": "Signature forgery",
    "impersonation": "Sender impersonation",
    "replay": "Replay attack",
    "unauthorized_verification": "Unauthorised verification",
    "channel_manipulation": "Quantum channel manipulation",
}

hero_header(
    "Scenario lab",
    "Run one scenario end-to-end: sign, distribute through the channel, verify, "
    "then inspect every signal from both detection layers.",
    badges=["Live engine", "seeded runs", "replay auto-seeds history"],
    icon="science",
)

with st.form("scenario_form"):
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_a:
        preset = st.selectbox("Channel preset", ["clean", "noisy", "degraded"], index=0)
    with col_b:
        attack = st.selectbox(
            "Scenario",
            scenario_options(),
            format_func=lambda key: ATTACK_TITLES.get(key, key),
        )
    with col_c:
        seed = st.number_input("Seed", min_value=1, max_value=2**31, value=20260101, step=1)
    submitted = st.form_submit_button("Run scenario", type="primary")

st.caption(scenario_description(attack))

if not submitted:
    empty_state(
        "Press Run scenario",
        "The verdict strip, signal tables and failed protocol checks will appear here.",
        icon="play_circle",
    )
    st.stop()

result = run_scenario_result(preset, attack, seed=int(seed))

detection = result["detection"]
stat_threat = detection["statistical"]["is_threat"]
pauli_threat = detection["pauli_measurement"]["is_threat"]
protocol_rejected = not result["accepted_by_protocol"]

# --------------------------------------------------------------------------- verdict strip
kcol = st.columns(4)
with kcol[0]:
    kpi("Protocol", "REJECT" if protocol_rejected else "ACCEPT",
        help="Classical rules: signature validity, freshness, authorisation, mismatch rate.",
        delta=f"mismatch rate {result['verification']['mismatch_rate']:.4f}",
        status="threat" if protocol_rejected else "safe",
        icon="verified_user")
with kcol[1]:
    kpi("Statistical", "THREAT" if stat_threat else "LEGITIMATE",
        help="Mismatch, QBER, per-basis QBER and distribution-distance signals.",
        status="threat" if stat_threat else "safe",
        icon="monitor_heart")
with kcol[2]:
    kpi("Pauli", "THREAT" if pauli_threat else "LEGITIMATE",
        help="Correlator agreement and retained-witness parity signals.",
        status="threat" if pauli_threat else "safe",
        icon="graphic_eq")
with kcol[3]:
    kpi("Runtime", f"{result['elapsed_seconds'] * 1000:.2f} ms",
        help="Wall-clock time for this single scenario run.",
        status="accent",
        icon="bolt")

# --------------------------------------------------------------------------- protocol verdict
verification = result["verification"]
mismatch_signal = next(
    (s for s in result["detection"]["statistical"]["signals"] if s["name"] == "mismatch_rate"),
    None,
)
mismatch_threshold = mismatch_signal["threshold"] if mismatch_signal else 0.05
with section_card(
    "Classical protocol verdict",
    "Independent of the two quantum detectors — these rules alone can stop replay and unauthorised verification.",
    icon="verified_user",
):
    chips = (
        f'<div class="qsg-chips">'
        f'<span class="qsg-chip">{"pass" if verification["signature_valid"] else "FAIL"} <span class="v">signature</span></span>'
        f'<span class="qsg-chip">{"pass" if verification["freshness_ok"] else "FAIL"} <span class="v">freshness</span></span>'
        f'<span class="qsg-chip">{"pass" if verification["authorisation_ok"] else "FAIL"} <span class="v">authorisation</span></span>'
        f'<span class="qsg-chip">{"pass" if verification["mismatch_rate"] <= mismatch_threshold else "FAIL"} <span class="v">mismatch rate</span></span>'
        f'</div>'
    )
    st.markdown(chips, unsafe_allow_html=True)
    if verification["reject_reason"]:
        callout(f"Reject reason: {verification['reject_reason']}", kind="threat")

# --------------------------------------------------------------------------- signal tables
stat_col, pauli_col = st.columns(2)
with stat_col, section_card("Method 1 — statistical signals", "Value vs threshold for every rule"):
    signals = result["detection"]["statistical"]["signals"]
    if signals:
        st.markdown(signal_progress(signals), unsafe_allow_html=True)
    else:
        empty_state("No signals", "This detector produced no signal rows.")

with pauli_col, section_card("Method 2 — Pauli measurement signals", "Value vs threshold for every rule"):
    signals = result["detection"]["pauli_measurement"]["signals"]
    if signals:
        st.markdown(signal_progress(signals), unsafe_allow_html=True)
    else:
        empty_state("No signals", "This detector produced no signal rows.")

# --------------------------------------------------------------------------- failing checks
failed = checks_frame(result)
with section_card("Failed protocol checks", "Only the checks that did not pass are listed."):
    if failed.empty:
        callout("All protocol checks passed — the transaction is legitimate on every classical rule.", kind="safe")
    else:
        styled_table(failed, badge_columns=["kind"])

# --------------------------------------------------------------------------- explain blind layer
explainer = pauli_explainer(attack)
if explainer and not pauli_threat and (stat_threat or protocol_rejected):
    callout(explainer, kind="info")