"""Design tokens and the shared Altair theme for the dashboard.

Visual styling is configured in ``.streamlit/config.toml`` (colors, fonts,
radii) and applied with native Streamlit components.  This module only holds
what Streamlit theming cannot express: the chart palette and the token set the
Altair theme reads so charts stay on-brand in both light and dark mode.
"""

from __future__ import annotations

from typing import Any

import altair as alt
import streamlit as st

# --------------------------------------------------------------------------- tokens

DARK = {
    "bg": "#0B1220",
    "surface": "#111A2E",
    "surface2": "#16223B",
    "border": "#24324F",
    "text": "#E6EDF7",
    "text2": "#93A4C3",
    "accent": "#22D3EE",
    "accent2": "#8B5CF6",
    "safe": "#22C55E",
    "threat": "#EF4444",
    "warning": "#F59E0B",
    "info": "#38BDF8",
    "grid": "#1B2A47",
    "label": "#93A4C3",
}

LIGHT = {
    "bg": "#F5F8FC",
    "surface": "#FFFFFF",
    "surface2": "#E9EFF7",
    "border": "#CBD8E8",
    "text": "#12203A",
    "text2": "#5B6B85",
    "accent": "#0891B2",
    "accent2": "#7C3AED",
    "safe": "#16A34A",
    "threat": "#DC2626",
    "warning": "#D97706",
    "info": "#0284C7",
    "grid": "#D6E1F0",
    "label": "#5B6B85",
}

# statistical = cyan, pauli = violet. DETECTOR_ORDER pins the palette index to
# each detector so Vega-Lite does not reorder them alphabetically.
DETECTOR_PALETTE = ["#22D3EE", "#8B5CF6"]
DETECTOR_ORDER = ["statistical", "pauli"]

# Semantic tone -> Streamlit's named color vocabulary, for st.badge.
TONE_COLOR = {
    "safe": "green",
    "threat": "red",
    "warning": "orange",
    "info": "blue",
    "accent": "primary",
    "accent2": "violet",
    "neutral": "gray",
}


def current_tokens() -> dict[str, str]:
    """Return the token set for the theme Streamlit is currently rendering."""
    try:
        return LIGHT if st.context.theme.type == "light" else DARK
    except Exception:  # outside a script run
        return DARK


# ------------------------------------------------------------------------- altair theme


def _is_light() -> bool:
    try:
        return st.context.theme.type == "light"
    except Exception:
        return False


def _altair_theme() -> dict[str, Any]:
    """Altair theme that mirrors the dashboard palette and typography."""
    tokens = LIGHT if _is_light() else DARK
    label = tokens["label"]
    return {
        "config": {
            "view": {"continuousWidth": 320, "continuousHeight": 260},
            "background": "transparent",
            "font": "Inter, -apple-system, sans-serif",
            "title": {
                "color": tokens["text"],
                "fontWeight": 600,
                "fontSize": 12,
                "anchor": "start",
            },
            "axis": {
                "labelColor": label,
                "titleColor": tokens["text"],
                "labelFontSize": 11,
                "titleFontSize": 11.5,
                "titleFontWeight": 600,
                "grid": True,
                "gridColor": tokens["grid"],
                "gridOpacity": 0.6,
                "domainColor": tokens["border"],
                "tickColor": tokens["border"],
            },
            "legend": {
                "labelColor": label,
                "titleColor": tokens["text"],
                "labelFontSize": 11,
                "titleFontSize": 11.5,
                "labelLimit": 220,
            },
            "range": {
                "category": DETECTOR_PALETTE,
                "ordinal": DETECTOR_PALETTE,
                "heatmap": [tokens["accent"], tokens["accent2"]],
            },
            "mark": {"color": tokens["accent"], "cornerRadius": 4},
            "bar": {
                "cornerRadiusTopLeft": 4,
                "cornerRadiusTopRight": 4,
            },
        }
    }


def register_altair_theme(name: str = "qsentinel") -> None:
    """Register and activate the dashboard Altair theme.

    Altair 6 exposes ``register`` as a decorator. The wrapped function runs each
    time a chart is compiled, so it reads the active Streamlit theme at render
    time and charts stay consistent when the user toggles light/dark.
    """
    if name not in alt.theme.names():

        @alt.theme.register(name, enable=True)
        def _adapter() -> dict[str, Any]:
            return _altair_theme()

    alt.theme.enable(name)
