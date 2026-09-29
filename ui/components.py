"""Reusable Streamlit components for the QuantumSigGuard dashboard.

Every component is pure presentation: it only formats and renders data passed
in from ``web_helpers`` / the pages.  Nothing here touches the engine.
"""

from __future__ import annotations

import html as _html
from contextlib import contextmanager
from typing import Any, Iterable, Sequence

import pandas as pd
import streamlit as st

from ui.theme import current_tokens, register_altair_theme

_MATERIAL = "'Material Symbols Outlined', 'Material Icons Outlined'"
_MONO = "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace"

# --------------------------------------------------------------------------- atoms


def _icon(name: str, extra: str = "") -> str:
    return f'<span class="m" style="font-family:{_MATERIAL};{extra}">{name}</span>'


def badge(kind: str) -> str:
    """Return one HTML badge for a verdict-style value.

    ``kind`` is normalised (upper); recognised values map to a semantic class
    plus a Material icon.  Any unknown value falls back to a neutral pill so
    the table never renders a bare uncoded string.
    """
    spec = {
        "THREAT": ("threat", "error"),
        "REJECT": ("threat", "block"),
        "REJECTED": ("threat", "block"),
        "SUSPECT": ("warning", "warning"),
        "LEGITIMATE": ("safe", "verified"),
        "ACCEPT": ("safe", "check_circle"),
        "ACCEPTED": ("safe", "check_circle"),
        "OK": ("safe", "check_circle"),
        "PAS": ("info", "help"),
        "INFO": ("info", "info"),
    }
    key = str(kind).upper()
    cls, icon = spec.get(key, ("neutral", "hollow_circle")) if key else ("neutral", "hollow_circle")
    return f'<span class="qsg-badge {cls}">{_icon(icon)}{_html.escape(str(kind))}</span>'


def verdict_badge(kind: str, size: str = "lg") -> str:
    """Large verdict badge used in hero verdict strips."""
    base = badge(kind)
    if size == "lg":
        base = base.replace('"qsg-badge ', '"qsg-badge lg ')
    return base


# --------------------------------------------------------------------------- layout


def hero_header(title: str, subtitle: str, badges: Sequence[str] | None = None,
                icon: str = "auto_awesome") -> None:
    toks = current_tokens()
    badge_html = "".join(f'<span class="qsg-badge {c}">{_icon(i)}{_html.escape(t)}</span>'
                         for t, c, i in _hero_badge_spec(badges or []))
    st.markdown(
        f"""
        <div class="qsg-hero">
          <div class="qsg-hero-icon">{_icon(icon)}</div>
          <div>
            <div class="qsg-hero-title">{_html.escape(title)}</div>
            <div class="qsg-hero-subtitle">{_html.escape(subtitle)}</div>
            <div class="qsg-hero-badges">{badge_html}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _hero_badge_spec(badges: Sequence[str]) -> list[tuple[str, str, str]]:
    """Map plain badge labels to (label, class, icon) tuples."""
    out = []
    for b in badges:
        u = b.upper()
        if "SEED" in u:
            out.append((b, "accent", "tag"))
        elif "STAT" in u or "DETECT" in u or "LEGIT" in u or "ACCEPT" in u:
            out.append((b, "safe", "verified"))
        elif "THREAT" in u or "REJECT" in u or "FALSE" in u or "ATTACK" in u:
            out.append((b, "threat", "error"))
        elif "WARN" in u or "MARGIN" in u or "EDGE" in u:
            out.append((b, "warning", "warning"))
        elif "PAULI" in u or "QUBIT" in u or "QBIT" in u or u.startswith("L=") or u.startswith("n=") or u.startswith("g="):
            out.append((b, "accent2", "dashboard"))
        else:
            out.append((b, "neutral", "hollow_circle"))
    return out


def kpi(label: str, value: str, help: str | None = None, delta: str | None = None,
        status: str = "accent", icon: str | None = None) -> None:
    """Custom KPI card. ``status`` controls the value tone: accent/safe/threat/warning/info."""
    cls = f"c-{status}" if status in {"safe", "threat", "warning", "info", "accent"} else ""
    icon_html = _icon(icon, "font-size:1.4rem;color:var(--qsg-accent);") if icon else ""
    help_attr = f' title="{_html.escape(help)}"' if help else ""
    delta_html = f'<div class="qsg-kpi-delta">{_html.escape(delta)}</div>' if delta else ""
    st.markdown(
        f"""
        <div class="qsg-kpi"{help_attr}>
          <div class="qsg-kpi-label">{icon_html}&nbsp;{_html.escape(label)}</div>
          <div class="qsg-kpi-value {cls}">{_html.escape(value)}</div>
          {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


@contextmanager
def section_card(title: str, description: str | None = None, icon: str = "category"):
    """Bordered card with a styled header; use as ``with section_card(...):``."""
    desc_html = f'<div class="qsg-section-desc">{_html.escape(description)}</div>' if description else ""
    with st.container(border=True):
        st.markdown(
            f'<div class="qsg-section-head"><div class="qsg-section-title">'
            f'{_icon(icon)}{_html.escape(title)}</div>{desc_html}</div>',
            unsafe_allow_html=True,
        )
        yield


def callout(text: str, kind: str = "info", icon: str | None = None) -> None:
    icons = {"info": "info", "warning": "warning", "threat": "error", "safe": "check_circle"}
    i = icon or icons.get(kind, "info")
    st.markdown(
        f'<div class="qsg-callout {kind}">{_icon(i)}{_html.escape(text)}</div>',
        unsafe_allow_html=True,
    )


def empty_state(title: str, message: str, icon: str = "inbox") -> None:
    st.markdown(
        f'<div class="qsg-empty">{_icon(icon)}<div style="font-weight:600;margin-top:.4rem">{_html.escape(title)}</div>'
        f'<div style="font-size:.82rem">{_html.escape(message)}</div></div>',
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- tables


def styled_table(
    df: pd.DataFrame,
    badge_columns: Iterable[str] = (),
    mono_columns: Iterable[str] | None = None,
    right_columns: Iterable[str] | None = None,
    threat_on: Iterable[str] = (),
    safe_on: Iterable[str] = (),
    empty_message: str = "No rows to display.",
) -> None:
    """Render a DataFrame as a styled HTML table.

    * ``badge_columns`` → cells rendered as semantic pills.
    * ``mono_columns``  → monospace tabular numerals.
    * ``right_columns`` → right aligned (numeric columns become mono+right by default).
    * ``threat_on`` / ``safe_on`` → columns whose values get a threat/safe tone.
    """
    df = df.reset_index(drop=True)
    if df.empty:
        empty_state("Nothing here", empty_message)
        return

    mono = set(mono_columns or ())
    right = set(right_columns or ())
    badge_cols = set(badge_columns or ())
    th = set(threat_on or ())
    sf = set(safe_on or ())

    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]) and not df[col].map(float("nan").__eq__).any():
            right.add(col)
            mono.add(col)

    def cell(col: str, val: Any) -> str:
        cls = []
        text = _html.escape("" if pd.isna(val) else str(val))
        classes = " ".join(cls)
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return f'<td class="muted">—</td>'
        if col in badge_cols:
            return f'<td>{badge(val)}</td>'
        td_class = []
        if col in mono:
            td_class.append("mono")
        if col in right:
            td_class.append("right")
        if col in th:
            td_class.append("row-threat")
        if col in sf:
            td_class.append("row-safe")
        if col not in mono and col not in right and not isinstance(val, float) and str(val).lower() in {"yes", "true", "no", "false"}:
            tone = "row-threat" if str(val).lower() in {"yes", "true"} else "row-safe"
            td_class.append(tone)
        return f'<td class="{" ".join(td_class)}">{text}</td>'

    head = "".join(f"<th>{_html.escape(str(c))}</th>" for c in df.columns)
    rows = "".join("<tr>" + "".join(cell(c, df.at[i, c]) for c in df.columns) + "</tr>" for i in range(len(df)))
    st.markdown(
        f'<div class="qsg-table-wrap"><table class="qsg-table"><thead><tr>{head}</tr></thead>'
        f"<tbody>{rows}</tbody></table></div>",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- signal bars


def signal_progress(signals: Sequence[dict]) -> str:
    """HTML progress rows for a detector's signal list.

    Each row: name, value/threshold (mono), and a bar showing how far the
    measured value sits against its threshold.  Tripped signals turn red.
    """
    toks = current_tokens()

    def row(s: dict) -> str:
        name = _html.escape(str(s.get("name", "?")))
        value = s.get("value")
        threshold = s.get("threshold")
        tripped = bool(s.get("tripped"))
        try:
            pct = (float(value) / float(threshold)) * 100.0 if threshold else 100.0
        except (TypeError, ValueError, ZeroDivisionError):
            pct = 100.0 if tripped else 0.0
        pct = max(0.0, min(100.0, pct))
        kind = "trip" if tripped else ("warn" if pct >= 80 or (pct <= 20) else "ok")
        v_str = _html.escape("—" if value is None else f"{value:.4f}")
        t_str = _html.escape("—" if threshold is None else f"{threshold:.4f}")
        status_text = "TRIPPED" if tripped else "within limit"
        return (
            f'<tr>'
            f'<td>{name}</td>'
            f'<td class="mono right">{v_str}</td>'
            f'<td class="mono right muted">{t_str}</td>'
            f'<td style="min-width:140px">'
            f'<div class="qsg-progress">'
            f'<div class="qsg-progress-track">'
            f'<div class="qsg-progress-fill {kind}" style="width:{pct:.0f}%"></div>'
            f'<div class="qsg-progress-threshold" style="left:100%"></div>'
            f'</div>'
            f'<div class="qsg-progress-pct">{status_text}</div>'
            f'</div>'
            f'</td>'
            f"</tr>"
        )

    body = "".join(row(s) for s in signals)
    return (
        '<div class="qsg-table-wrap"><table class="qsg-table">'
        "<thead><tr><th>Signal</th><th>Value</th><th>Threshold</th><th style=\"white-space:nowrap\">vs limit</th></tr></thead>"
        f"<tbody>{body}</tbody></table></div>"
    )


def kpi_row(cards: Sequence[dict]) -> None:
    """Render several ``kpi`` specs in a wrapping flex row (stacks on tablets)."""
    cards_html = "".join(
        f'<div style="display:flex;flex-direction:column;justify-content:space-between;gap:0.3rem;'
        f'border:1px solid var(--qsg-border);border-radius:var(--qsg-radius);background:var(--qsg-surface);'
        f'padding:1rem 1.15rem;flex:1 1 200px;min-width:190px">'
        f'<div style="font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--qsg-text2)">'
        f'{_icon(c.get("icon")) if c.get("icon") else ""}{_html.escape(c["label"])}</div>'
        f'<div style="font-family:{_MONO};font-size:1.55rem;font-weight:600;color:var(--qsg-text)">{_html.escape(str(c["value"]))}</div>'
        f'<div style="font-size:.72rem;color:var(--qsg-text2)">{_html.escape(c.get("delta") or "")}</div>'
        f'</div>'
        for c in cards
    )
    st.markdown(
        f'<div style="display:flex;flex-wrap:wrap;gap:.75rem;margin-bottom:1rem">{cards_html}</div>',
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- charts


def prepare_theme() -> None:
    """Ensure our Altair theme is registered and active (idempotent)."""
    register_altair_theme()


def detector_rate_chart(df: pd.DataFrame, *, title: str = "Detection rate by attack class") -> Any:
    """Horizontal bar chart of detection rates per attack class (0–1 domain)."""
    import altair as alt

    base = alt.Chart(df).encode(
        y=alt.Y("attack:N", title=None, sort="-x", axis=alt.Axis(labelLimit=220)),
        x=alt.X("rate:Q", title="Detection rate", scale=alt.Scale(domain=[0, 1])),
        color=alt.Color("method:N", legend=None),
        tooltip=["attack:N", "method:N", alt.Tooltip("rate:Q", format=".3f")],
    )
    bars = base.mark_bar(cornerRadius=4)
    labels = base.mark_text(
        dx=-6, align="right", color="#93A4C3", font="JetBrains Mono, monospace", fontSize=10,
    ).encode(text=alt.Text("rate:Q", format=".3f"))
    chart = (bars + labels).properties(title=title, height=alt.Step(22))
    return chart


def rate_line_chart(df: pd.DataFrame, *, x: str, x_title: str, y: str = "detection_rate:Q",
                    series: str = "structure:N", title: str = "",
                    threshold: float | None = None) -> Any:
    """Line chart for noise / group sweeps, one line per detector structure.

    If ``threshold`` is given, a dashed reference rule and value label are drawn.
    """
    import altair as alt

    base = alt.Chart(df).properties(title=title)
    lines = base.encode(
        x=alt.X(x, title=x_title),
        y=alt.Y(y, title="Detection rate", scale=alt.Scale(domain=[0, 1])),
        color=alt.Color(series, legend=alt.Legend(title="Detector")),
    ).mark_line(strokeWidth=2.2).encode()

    dots = base.encode(
        x=alt.X(x, title=x_title),
        y=alt.Y(y, title="Detection rate"),
        color=alt.Color(series, legend=None),
    ).mark_point(size=34, filled=True, opacity=0.9).encode()

    layers = [lines, dots]
    if threshold is not None and not df.empty:
        rule_data = pd.DataFrame({
            "t": [threshold],
            "yn": [1.0],
            "label": [f"threshold {threshold:.3f}"],
        })
        rule = alt.Chart(rule_data).mark_rule(
            strokeDash=[4, 4], color="#F59E0B", opacity=0.8
        ).encode(
            x=alt.X("t:Q"),
            y=alt.Y("yn:Q", axis=None, scale=alt.Scale(domain=[0, 1])),
        )
        label = alt.Chart(rule_data).mark_text(
            dx=-6, dy=-6, align="right", color="#F59E0B", fontSize=10,
            font="Inter, sans-serif", fontWeight=600,
        ).encode(
            x=alt.X("t:Q"),
            y=alt.Y("yn:Q", axis=None),
            text="label:N",
        )
        layers.append(rule)
        layers.append(label)
    return alt.layer(*layers)


__all__ = [
    "badge", "verdict_badge", "hero_header", "kpi", "section_card", "callout",
    "empty_state", "styled_table", "signal_progress", "kpi_row", "prepare_theme",
    "detector_rate_chart", "rate_line_chart",
]