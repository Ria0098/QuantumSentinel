"""QuantumSigGuard web dashboard entry point.

Run from the repository root::

    streamlit run streamlit_app.py

Three pages: an overview of the pre-generated ``results/`` bundle, an
interactive scenario lab, and a configurable controlled evaluation.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

import streamlit as st

from ui.components import prepare_theme

try:
    _QSG_VERSION = version("qsentinel")
except PackageNotFoundError:  # running from source without install
    _QSG_VERSION = "source"

st.set_page_config(
    page_title="QuantumSigGuard",
    page_icon=":material/shield:",
    layout="wide",
    initial_sidebar_state="expanded",
)

prepare_theme()

st.navigation(
    [
        st.Page("app_pages/overview.py", title="Overview", icon=":material/dashboard:", default=True),
        st.Page("app_pages/scenario_lab.py", title="Scenario lab", icon=":material/science:"),
        st.Page("app_pages/evaluation.py", title="Evaluation", icon=":material/analytics:"),
    ]
).run()

with st.sidebar:
    st.markdown("### QuantumSigGuard")
    st.caption(f"SIH 2026 · SIH26141 · v{_QSG_VERSION}")

    st.divider()

    st.markdown("**At a glance**")
    st.markdown(
        f"- Architecture — statistical + Pauli\n"
        f"- ML/AI — none, rule-based only\n"
        f"- Scenarios — 5 attacks + legitimate\n"
        f"- Determinism — seeded experiments\n"
        f"- Threshold rules — 12 across both layers"
    )

    st.divider()

    st.markdown("**Performance**")
    st.markdown(
        "- Mean per transaction — ~10–12 ms\n"
        "- 1,200 transactions — ~2–3 seconds\n"
        "- Noise sweep — reproducible\n"
        "- Group sweep — g = 1 to 4"
    )

    st.divider()
    st.caption("View layer only. Every value is read from the engine; the UI computes no verdicts.")
