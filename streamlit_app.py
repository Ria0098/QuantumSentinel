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
from ui.theme import inject_css

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
inject_css()

_brand = (
    '<div class="qsg-brand">'
    '<div class="qsg-brand-mark"><span class="m" style="font-family:\'Material Symbols Outlined\'">'
    "auto_awesome</span></div>"
    '<div><div class="qsg-brand-name">QuantumSigGuard</div>'
    f'<div class="qsg-brand-tag">SIH26141 &middot; v{_QSG_VERSION}</div></div>'
    "</div>"
)
st.sidebar.markdown(_brand, unsafe_allow_html=True)

nav = st.navigation(
    [
        st.Page(
            "app_pages/overview.py",
            title="Overview",
            icon=":material/dashboard:",
            default=True,
        ),
        st.Page(
            "app_pages/scenario_lab.py",
            title="Scenario lab",
            icon=":material/science:",
        ),
        st.Page(
            "app_pages/evaluation.py",
            title="Evaluation",
            icon=":material/analytics:",
        ),
    ]
)
nav.run()

st.markdown(
    '<div class="qsg-footer">SIH 2026 &middot; SIH26141 &middot; Egreen Quanta LLP '
    "&middot; quantum-channel signature verification with statistical + Pauli detection</div>",
    unsafe_allow_html=True,
)