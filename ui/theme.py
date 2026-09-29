"""Design tokens, global CSS and the shared Altair theme for the dashboard.

Palette, typography and radii live here once, exposed as tokens, so every
component and chart draws from the same vocabulary.  ``inject_css()`` emits a
single ``<style>`` block scoped to the active theme (dark or light) and
registers a matching Altair theme so native charts stay on-palette too.
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
    "chart_safe": "#22D3EE",
    "chart_threat": "#EF4444",
    "glow": "rgba(34, 211, 238, 0.10)",
}

LIGHT = {
    "bg": "#F5F8FC",
    "surface": "#FFFFFF",
    "surface2": "#E9EFF7",
    "border": "#CBD8E8",
    "text": "#12203A",
    "text2": "#5B6B85",
    "accent": "#0E7490",
    "accent2": "#7C3AED",
    "safe": "#16A34A",
    "threat": "#DC2626",
    "warning": "#D97706",
    "info": "#0284C7",
    "grid": "#D6E1F0",
    "chart_safe": "#0891B2",
    "chart_threat": "#DC2626",
    "glow": "rgba(14, 116, 144, 0.08)",
}

DETECTOR_PALETTE = ["#22D3EE", "#8B5CF6"]  # statistical = cyan, pauli = violet


def current_tokens() -> dict[str, str]:
    """Return the token set for the theme Streamlit is currently rendering."""
    try:
        return LIGHT if st.context.theme.type == "light" else DARK
    except Exception:  # outside a script run
        return DARK


# ------------------------------------------------------------------------- global css

_CSS_TEMPLATE = """
<style>
:root {{
  --qsg-bg: {bg};
  --qsg-surface: {surface};
  --qsg-surface2: {surface2};
  --qsg-border: {border};
  --qsg-text: {text};
  --qsg-text2: {text2};
  --qsg-accent: {accent};
  --qsg-accent2: {accent2};
  --qsg-safe: {safe};
  --qsg-threat: {threat};
  --qsg-warning: {warning};
  --qsg-info: {info};
  --qsg-glow: {glow};
  --qsg-radius: 12px;
  --qsg-radius-sm: 8px;
  --qsg-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
}}

/* ---------- app surface -------------------------------------------------- */
html, body {{
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  color: var(--qsg-text);
}}
[data-testid="stAppViewContainer"] > .main,
[data-testid="stAppViewContainer"] .block-container {{
  background: var(--qsg-bg);
}}
[data-testid="stHeader"] {{
  background: transparent;
}}
[data-testid="stSidebar"] {{
  background: var(--qsg-surface);
  border-right: 1px solid var(--qsg-border);
}}
[data-testid="stSidebar"] a {{
  color: var(--qsg-text2);
}}
[data-testid="stSidebar"] a:hover {{
  color: var(--qsg-text);
}}

/* ---------- hide streamlit chrome ---------------------------------------- */
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"] {{
  visibility: hidden;
  height: 0px;
}}

/* ---------- typography ---------------------------------------------------- */
h1, h2, h3, h4, h5, h6 {{
  font-family: 'Inter', -apple-system, sans-serif;
  letter-spacing: -0.01em;
}}

/* ---------- hero banner ---------------------------------------------------- */
.qsg-hero {{
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding: 1.5rem 1.75rem;
  border: 1px solid var(--qsg-border);
  border-radius: var(--qsg-radius);
  background: linear-gradient(135deg, var(--qsg-surface) 0%, var(--qsg-surface2) 100%);
  box-shadow: 0 8px 24px -12px var(--qsg-glow);
  margin-bottom: 1.25rem;
}}
.qsg-hero-icon {{
  width: 52px; height: 52px; flex: 0 0 52px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 14px;
  background: var(--qsg-glow);
  color: var(--qsg-accent);
  font-size: 1.5rem;
}}
.qsg-hero-title {{
  font-size: 1.5rem; font-weight: 700; color: var(--qsg-text);
  margin: 0; line-height: 1.2;
}}
.qsg-hero-subtitle {{
  font-size: 0.9rem; color: var(--qsg-text2); margin-top: 0.2rem;
}}
.qsg-hero-badges {{
  display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.7rem;
}}

/* ---------- badges / pills ------------------------------------------------- */
.qsg-badge {{
  display: inline-flex; align-items: center; gap: 0.30rem;
  padding: 0.16rem 0.6rem; border-radius: 999px;
  font-size: 0.72rem; font-weight: 600; letter-spacing: 0.02em;
  border: 1px solid transparent; white-space: nowrap;
}}
.qsg-badge .m {{
  font-size: 0.85rem;
}}
.qsg-badge.neutral {{ border-color: var(--qsg-border); color: var(--qsg-text2); background: var(--qsg-surface2); }}
.qsg-badge.accent {{ color: var(--qsg-accent); background: color-mix(in srgb, var(--qsg-accent) 12%, transparent); border-color: color-mix(in srgb, var(--qsg-accent) 40%, transparent); }}
.qsg-badge.accent2 {{ color: var(--qsg-accent2); background: color-mix(in srgb, var(--qsg-accent2) 12%, transparent); border-color: color-mix(in srgb, var(--qsg-accent2) 40%, transparent); }}
.qsg-badge.safe {{ color: var(--qsg-safe); background: color-mix(in srgb, var(--qsg-safe) 12%, transparent); border-color: color-mix(in srgb, var(--qsg-safe) 40%, transparent); }}
.qsg-badge.threat {{ color: var(--qsg-threat); background: color-mix(in srgb, var(--qsg-threat) 12%, transparent); border-color: color-mix(in srgb, var(--qsg-threat) 40%, transparent); }}
.qsg-badge.warning {{ color: var(--qsg-warning); background: color-mix(in srgb, var(--qsg-warning) 12%, transparent); border-color: color-mix(in srgb, var(--qsg-warning) 40%, transparent); }}
.qsg-badge.info {{ color: var(--qsg-info); background: color-mix(in srgb, var(--qsg-info) 12%, transparent); border-color: color-mix(in srgb, var(--qsg-info) 40%, transparent); }}
.qsg-badge.lg {{ font-size: 0.85rem; padding: 0.28rem 0.85rem; }}

/* ---------- KPI cards ------------------------------------------------------- */
.qsg-kpi {{
  border: 1px solid var(--qsg-border);
  border-radius: var(--qsg-radius);
  background: var(--qsg-surface);
  padding: 1rem 1.15rem;
  height: 100%;
  display: flex; flex-direction: column; justify-content: space-between; gap: 0.3rem;
}}
.qsg-kpi-label {{
  font-size: 0.78rem; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.06em; color: var(--qsg-text2);
}}
.qsg-kpi-value {{
  font-family: var(--qsg-mono);
  font-size: 1.7rem; font-weight: 600; color: var(--qsg-text);
  line-height: 1.1; white-space: nowrap;
}}
.qsg-kpi-delta {{
  font-size: 0.78rem; color: var(--qsg-text2);
}}
.qsg-kpi-value.c-safe {{ color: var(--qsg-safe); }}
.qsg-kpi-value.c-threat {{ color: var(--qsg-threat); }}
.qsg-kpi-value.c-warning {{ color: var(--qsg-warning); }}
.qsg-kpi-value.c-info {{ color: var(--qsg-info); }}
.qsg-kpi-value.c-accent {{ color: var(--qsg-accent); }}

/* ---------- section cards --------------------------------------------------- */
.qsg-section-head {{
  display: flex; align-items: baseline; justify-content: space-between; gap: 1rem;
  margin-bottom: 0.35rem;
}}
.qsg-section-title {{
  display: flex; align-items: center; gap: 0.5rem;
  font-size: 1.0rem; font-weight: 700; color: var(--qsg-text);
}}
.qsg-section-title .m {{ color: var(--qsg-accent); font-size: 1.15rem; }}
.qsg-section-desc {{
  font-size: 0.82rem; color: var(--qsg-text2); margin-top: 0.15rem;
}}

/* ---------- styled tables ---------------------------------------------------- */
.qsg-table {{
  width: 100%; border-collapse: collapse; font-size: 0.86rem;
}}
.qsg-table th {{
  text-align: left; font-size: 0.72rem; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.05em; color: var(--qsg-text2);
  padding: 0.45rem 0.7rem; border-bottom: 1px solid var(--qsg-border);
}}
.qsg-table td {{
  padding: 0.5rem 0.7rem; border-bottom: 1px solid color-mix(in srgb, var(--qsg-border) 55%, transparent);
  color: var(--qsg-text); vertical-align: middle;
}}
.qsg-table tr:last-child td {{ border-bottom: none; }}
.qsg-table tr:hover td {{ background: color-mix(in srgb, var(--qsg-surface2) 65%, transparent); }}
.qsg-table td.mono {{ font-family: var(--qsg-mono); font-variant-numeric: tabular-nums; }}
.qsg-table td.right {{ text-align: right; }}
.qsg-table td.muted {{ color: var(--qsg-text2); }}
.qsg-table td.row-threat {{ color: var(--qsg-threat); }}
.qsg-table td.row-safe {{ color: var(--qsg-safe); }}
.qsg-table-wrap {{
  overflow-x: auto; border: 1px solid var(--qsg-border); border-radius: var(--qsg-radius-sm);
  background: var(--qsg-surface);
}}

/* ---------- progress bar (signal value vs threshold) ------------------------ */
.qsg-progress {{
  display: inline-flex; align-items: center; gap: 0.5rem; width: 100%;
}}
.qsg-progress-track {{
  flex: 1; height: 6px; border-radius: 999px;
  background: var(--qsg-surface2); position: relative; overflow: hidden;
}}
.qsg-progress-fill {{
  height: 100%; border-radius: 999px;
}}
.qsg-progress-fill.ok {{ background: var(--qsg-safe); }}
.qsg-progress-fill.warn {{ background: var(--qsg-warning); }}
.qsg-progress-fill.trip {{ background: var(--qsg-threat); }}
.qsg-progress-threshold {{
  position: absolute; top: -3px; bottom: -3px; width: 2px;
  background: var(--qsg-text2); opacity: 0.9;
}}
.qsg-progress-pct {{
  font-family: var(--qsg-mono); font-size: 0.72rem; color: var(--qsg-text2);
  min-width: 3.2rem; text-align: right;
}}

/* ---------- chips (small protocol status) ----------------------------------- */
.qsg-chips {{
  display: flex; flex-wrap: wrap; gap: 0.5rem;
}}
.qsg-chip {{
  display: inline-flex; align-items: center; gap: 0.35rem;
  padding: 0.3rem 0.7rem; border-radius: var(--qsg-radius-sm);
  font-size: 0.8rem; border: 1px solid var(--qsg-border);
  background: var(--qsg-surface2); color: var(--qsg-text);
}}
.qsg-chip .m {{ font-size: 1rem; }}
.qsg-chip .v {{ font-family: var(--qsg-mono); font-weight: 600; }}

/* ---------- callouts / empty states ------------------------------------------ */
.qsg-callout {{
  display: flex; gap: 0.6rem; align-items: flex-start;
  padding: 0.7rem 0.85rem; border-radius: var(--qsg-radius-sm);
  border: 1px solid; font-size: 0.86rem; line-height: 1.45;
}}
.qsg-callout .m {{ font-size: 1.1rem; margin-top: 1px; }}
.qsg-callout.info {{ border-color: color-mix(in srgb, var(--qsg-info) 45%, transparent); background: color-mix(in srgb, var(--qsg-info) 10%, transparent); color: var(--qsg-text); }}
.qsg-callout.warning {{ border-color: color-mix(in srgb, var(--qsg-warning) 45%, transparent); background: color-mix(in srgb, var(--qsg-warning) 10%, transparent); color: var(--qsg-text); }}
.qsg-callout.threat {{ border-color: color-mix(in srgb, var(--qsg-threat) 45%, transparent); background: color-mix(in srgb, var(--qsg-threat) 10%, transparent); color: var(--qsg-text); }}
.qsg-callout.safe {{ border-color: color-mix(in srgb, var(--qsg-safe) 45%, transparent); background: color-mix(in srgb, var(--qsg-safe) 10%, transparent); color: var(--qsg-text); }}

.qsg-empty {{
  text-align: center; padding: 1.6rem 1rem; color: var(--qsg-text2);
  border: 1px dashed var(--qsg-border); border-radius: var(--qsg-radius-sm);
}}
.qsg-empty .m {{ font-size: 1.7rem; color: var(--qsg-accent); }}

/* ---------- buttons ----------------------------------------------------------- */
.st-key-launch button {{ background: var(--qsg-accent); color: #04121F; font-weight: 700; border: none; }}
.st-key-launch button:hover {{ background: color-mix(in srgb, var(--qsg-accent) 85%, white); color: #04121F; }}

/* ---------- sidebar brand ------------------------------------------------------ */
.qsg-brand {{
  display: flex; align-items: center; gap: 0.7rem; padding: 0.4rem 0 1rem 0;
  border-bottom: 1px solid var(--qsg-border); margin-bottom: 0.9rem;
}}
.qsg-brand-mark {{
  width: 38px; height: 38px; flex: 0 0 38px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, var(--qsg-accent), var(--qsg-accent2));
  color: #04121F; font-size: 1.15rem;
}}
.qsg-brand-name {{ font-weight: 700; font-size: 0.98rem; color: var(--qsg-text); }}
.qsg-brand-tag {{ font-size: 0.7rem; color: var(--qsg-text2); }}

/* ---------- footer -------------------------------------------------------------- */
.qsg-footer {{
  margin-top: 2.5rem; padding-top: 1rem; border-top: 1px solid var(--qsg-border);
  font-size: 0.72rem; color: var(--qsg-text2); text-align: center;
}}

/* ---------- metric & dataframe tweaks ------------------------------------------- */
[data-testid="stMetric"] {{
  background: var(--qsg-surface); border: 1px solid var(--qsg-border);
  border-radius: var(--qsg-radius); padding: 0.6rem 0.85rem;
}}
[data-testid="stMetricLabel"] {{ color: var(--qsg-text2); }}
[data-testid="stMetricValue"] {{ color: var(--qsg-text); font-family: var(--qsg-mono); }}
[data-testid="stDataFrame"] {{ border: 1px solid var(--qsg-border); border-radius: var(--qsg-radius-sm); }}
[data-testid="stDataFrame"] thead th {{ text-transform: uppercase; font-size: 0.72rem; letter-spacing: 0.04em; }}
[data-testid="stExpander"] details {{ border: 1px solid var(--qsg-border); border-radius: var(--qsg-radius-sm); background: var(--qsg-surface); }}

/* ---------- responsive ------------------------------------------------------------- */
@media (max-width: 900px) {{
  .qsg-hero {{ flex-direction: column; align-items: flex-start; }}
}}
</style>
"""


def inject_css() -> None:
    """Inject the global stylesheet for the theme currently being rendered."""
    st.markdown(_CSS_TEMPLATE.format(**current_tokens()), unsafe_allow_html=True)


# ------------------------------------------------------------------------- altair theme


def _is_light() -> bool:
    try:
        return st.context.theme.type == "light"
    except Exception:
        return False


def _altair_theme() -> dict[str, Any]:
    """Altair theme that mirrors the dashboard palette and typography."""
    light = _is_light()
    tokens = LIGHT if light else DARK
    label = tokens["text2"]
    grid = tokens["grid"]
    return {
        "config": {
            "view": {"continuousWidth": 320, "continuousHeight": 260},
            "background": "transparent",
            "font": "Inter, -apple-system, sans-serif",
            "title": {
                "color": tokens["text"],
                "fontWeight": 650,
                "fontSize": 13,
                "anchor": "start",
            },
            "axis": {
                "labelColor": label,
                "titleColor": tokens["text"],
                "labelFontSize": 11,
                "titleFontSize": 11.5,
                "titleFontWeight": 600,
                "grid": True,
                "gridColor": grid,
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
            "mark": {
                "color": tokens["accent"],
                "cornerRadius": 4,
            },
            "bar": {
                "cornerRadiusTopLeft": 4,
                "cornerRadiusTopRight": 4,
            },
        }
    }


def register_altair_theme(name: str = "qsentinel") -> None:
    """Register and activate the dashboard Altair theme.

    Altair 6 exposes ``register`` as a decorator (optionally with ``enable=True``).
    The wrapped function is invoked each time a chart is compiled, so it reads
    the active Streamlit theme at render time — keeping charts consistent when
    the user toggles light/dark.
    """
    if name not in alt.theme.names():

        @alt.theme.register(name, enable=True)
        def _adapter() -> dict[str, Any]:
            return _altair_theme()

    alt.theme.enable(name)