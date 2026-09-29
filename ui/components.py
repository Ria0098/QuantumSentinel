"""Reusable Streamlit components for the QuantumSigGuard dashboard.

Every component is pure presentation built from native Streamlit elements
(``st.metric``, ``st.badge``, ``st.dataframe``, ``st.container``) so the app
inherits theming, accessibility and layout behaviour from the framework instead
of hand-rolled HTML.  Nothing here touches the detection engine.
"""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import contextmanager
from typing import Any, Iterator

import pandas as pd
import streamlit as st

from ui.theme import DETECTOR_ORDER, TONE_COLOR, register_altair_theme

# --------------------------------------------------------------------------- atoms

# Verdict-style value -> (semantic tone, Material icon).
_VERDICTS: dict[str, tuple[str, str]] = {
    "THREAT": ("threat", "error"),
    "ATTACK": ("threat", "gpp_maybe"),
    "REJECT": ("threat", "block"),
    "REJECTED": ("threat", "block"),
    "SUSPECT": ("warning", "warning"),
    "LEGITIMATE": ("safe", "verified"),
    "BENIGN": ("safe", "verified"),
    "ACCEPT": ("safe", "check_circle"),
    "ACCEPTED": ("safe", "check_circle"),
    "OK": ("safe", "check_circle"),
    "STATISTICAL": ("accent", "monitor_heart"),
    "PAULI": ("accent2", "graphic_eq"),
    "PAULI MEASUREMENT": ("accent2", "graphic_eq"),
    "INFO": ("info", "info"),
    "PAS": ("info", "help"),
    "FAIL": ("threat", "cancel"),
    "FAILED": ("threat", "cancel"),
    "ERROR": ("threat", "error"),
    "MISSING": ("warning", "warning"),
}

# Tone -> default Material icon, used when a chip is given an explicit tone.
_TONE_ICON = {
    "threat": "error",
    "warning": "warning",
    "safe": "check_circle",
    "accent": "monitor_heart",
    "accent2": "graphic_eq",
    "info": "info",
    "neutral": "circle",
}


def verdict_tone(kind: str) -> tuple[str, str]:
    """Map a verdict label to ``(semantic tone, Material icon)``.

    Unknown values fall back to a neutral pill so nothing renders uncoded.
    """
    key = str(kind).upper()
    return _VERDICTS.get(key, ("neutral", "circle"))


def badge(kind: str) -> Any:
    """A single :class:`st.badge` for a verdict-style value."""
    tone, icon = verdict_tone(kind)
    return st.badge(str(kind), icon=f":material/{icon}:", color=TONE_COLOR[tone])


def chip(label: str, tone: str | None = None, icon: str | None = None) -> Any:
    """One badge. ``tone``/``icon`` default to the verdict mapping for ``label``."""
    if tone is None:
        tone, default_icon = verdict_tone(label)
    else:
        default_icon = _TONE_ICON.get(tone, "circle")
    return st.badge(
        str(label),
        icon=f":material/{icon or default_icon}:",
        color=TONE_COLOR.get(tone, TONE_COLOR["neutral"]),
    )


def badges(items: Sequence[str | tuple[str, str]]) -> None:
    """A horizontal row of :class:`st.badge` chips.

    Each item is either a plain string (tone derived from the verdict mapping)
    or an explicit ``(label, tone)`` pair, for status that is not a verdict.
    """
    with st.container(horizontal=True, gap="small"):
        for item in items:
            if isinstance(item, (tuple, list)):
                chip(str(item[0]), str(item[1]))
            else:
                chip(str(item))


# --------------------------------------------------------------------------- layout


def page_header(
    title: str,
    subtitle: str,
    *,
    icon: str = "monitor_heart",
    chips: Sequence[str | tuple[str, str]] = (),
    meta: Sequence[str] = (),
) -> None:
    """Page title, one-line description, status badges and a metadata line.

    ``chips`` carries status (coloured, semantic). ``meta`` carries run
    configuration - seed, protocol parameters, counts - which is reference data
    rather than a status, so it renders as quiet caption text.
    """
    st.title(title, icon=f":material/{icon}:")
    st.caption(subtitle)
    if chips:
        badges(chips)
    if meta:
        st.caption(" · ".join(str(m) for m in meta))


def section_card(
    title: str, description: str | None = None, *, icon: str = "crop_square"
) -> Any:
    """Bordered card with a titled header. Use as ``with section_card(...):``.

    Returns a context manager; the description renders under the title so the
    card's contents stay the only thing below the fold of the header.
    """
    return _SectionCard(title, description, icon)


class _SectionCard:
    """``st.container(border=True)`` with a header, usable via ``with``."""

    def __init__(self, title: str, description: str | None, icon: str) -> None:
        self._title = title
        self._description = description
        self._icon = icon

    def __enter__(self) -> "st.container":
        self._container = st.container(border=True)
        st.subheader(self._title, icon=f":material/{self._icon}:")
        if self._description:
            st.caption(self._description)
        return self._container

    def __exit__(self, *exc: object) -> None:
        return None


def pipeline(steps: Sequence[tuple[str, str, str]], *, title: str = "Flow") -> None:
    """Horizontal pipeline of the QDS stages.

    ``steps`` is a sequence of ``(label, detail, icon)`` tuples. Each stage is a
    bordered container inside a wrapping horizontal row, so it reflows instead
    of overflowing on narrow screens.
    """
    with section_card(title, "How a transaction moves through the framework", icon="account_tree"):
        with st.container(horizontal=True, gap="small"):
            for label, detail, icon in steps:
                with st.container(border=True):
                    st.markdown(f":material/{icon}:", help=detail)
                    st.markdown(f"**{label}**")
                    st.caption(detail)


def kpi_row(cards: Sequence[dict[str, Any]]) -> None:
    """A responsive row of :class:`st.metric` cards.

    Each card spec accepts ``label``, ``value``, ``help``, ``delta``,
    ``delta_color`` and ``icon``.  A wrapping horizontal container is used rather
    than ``st.columns`` so the row reflows on smaller screens.
    """
    with st.container(horizontal=True, gap="medium"):
        for card in cards:
            st.metric(
                card["label"],
                card["value"],
                card.get("delta"),
                delta_color=card.get("delta_color", "off"),
                help=card.get("help"),
                icon=card.get("icon"),
                border=True,
            )


def kpi(
    label: str,
    value: str,
    *,
    help: str | None = None,
    delta: str | None = None,
    tone: str = "accent",
    icon: str | None = None,
) -> None:
    """Single :class:`st.metric` card, with the delta coloured by ``tone``.

    ``tone`` is semantic (``safe``/``threat``/``warning``/``info``/``accent``)
    and maps onto Streamlit's ``delta_color``.
    """
    st.metric(
        label,
        value,
        delta,
        delta_color=_DELTA_COLOR.get(tone, "off"),
        help=help,
        icon=f":material/{icon}:" if icon else None,
        border=True,
    )


_DELTA_COLOR = {
    "safe": "normal",
    "threat": "inverse",
    "warning": "off",
    "info": "off",
    "accent": "off",
}


def callout(text: str, kind: str = "info", *, icon: str | None = None) -> None:
    """An inline informational / warning / success callout."""
    mapping = {
        "info": (st.info, "info"),
        "warning": (st.warning, "warning"),
        "threat": (st.error, "error"),
        "safe": (st.success, "check_circle"),
    }
    fn, default_icon = mapping.get(kind, mapping["info"])
    fn(text, icon=f":material/{icon or default_icon}:")


def empty_state(title: str, message: str, *, icon: str = "inbox") -> None:
    """Placeholder shown when there is nothing to display yet."""
    with st.container(border=True):
        st.markdown(f":material/{icon}:", help=title)
        st.markdown(f"**{title}**")
        st.caption(message)


# --------------------------------------------------------------------------- tables

# Text columns that are actually enumerated values, not free text.
_LABEL_COLUMNS = {
    "detector", "scenario", "attack", "ground truth", "statistical", "pauli",
    "protocol", "kind", "rule", "label", "state", "tripped", "signature_valid",
    "freshness_ok", "authorisation_ok", "comparison",
}


def _column_config(df: pd.DataFrame, help: dict[str, str] | None = None) -> dict[str, Any]:
    """Build ``column_config`` from the frame's dtypes and column names."""
    help = help or {}
    config: dict[str, Any] = {}
    for col in df.columns:
        tooltip = help.get(col)
        series = df[col]
        if col in _LABEL_COLUMNS or not pd.api.types.is_numeric_dtype(series):
            config[col] = st.column_config.TextColumn(help=tooltip, width="medium")
            continue
        # Integers read better without decimals; a float column whose values are
        # all whole numbers (trials, detected, rejected) is a count too.
        is_count = pd.api.types.is_integer_dtype(series) or (
            series.dropna().mod(1).eq(0).all() if not series.empty else False
        )
        config[col] = st.column_config.NumberColumn(
            format="%d" if is_count else "%.4f", help=tooltip, width="small"
        )
    return config


def styled_table(
    df: pd.DataFrame,
    *,
    empty_message: str = "No rows to display.",
    help: dict[str, str] | None = None,
) -> None:
    """Render a DataFrame with native formatting.

    Column types are inferred, so callers pass the frame as produced by
    ``web_helpers`` and get aligned, consistently formatted output without
    hand-writing a format string per column. ``help`` attaches per-column
    tooltips.
    """
    if df.empty:
        empty_state("Nothing here", empty_message)
        return
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        column_config=_column_config(df, help),
    )


def signal_table(signals: Sequence[dict]) -> pd.DataFrame:
    """Frame of one detector's signals, ready for :func:`styled_table`.

    Adds a ``vs limit`` progress column (value as a fraction of its own
    threshold, capped at 1.0) so a reader can see how close each signal is to
    tripping. The ``state`` column carries the verdict as text, so meaning never
    depends on colour alone.
    """
    rows = []
    for signal in signals:
        value = signal.get("value")
        threshold = signal.get("threshold")
        try:
            ratio = float(value) / float(threshold) if threshold else (1.0 if signal.get("tripped") else 0.0)
        except (TypeError, ValueError, ZeroDivisionError):
            ratio = 1.0 if signal.get("tripped") else 0.0
        rows.append(
            {
                "signal": signal.get("name", "?"),
                "value": round(float(value), 4) if value is not None else None,
                "rule": signal.get("comparison", ""),
                "threshold": round(float(threshold), 4) if threshold is not None else None,
                "vs limit": round(min(max(ratio, 0.0), 1.0), 4),
                "state": "TRIPPED" if signal.get("tripped") else "ok",
            }
        )
    return pd.DataFrame(
        rows,
        columns=["signal", "value", "rule", "threshold", "vs limit", "state"],
    )


def signal_config() -> dict[str, Any]:
    """``column_config`` for a frame built by :func:`signal_table`."""
    return {
        "signal": st.column_config.TextColumn("Signal", width="large"),
        "value": st.column_config.NumberColumn("Value", format="%.4f", width="small"),
        "rule": st.column_config.TextColumn("Rule", width="small"),
        "threshold": st.column_config.NumberColumn("Threshold", format="%.4f", width="small"),
        "vs limit": st.column_config.ProgressColumn(
            "vs limit",
            min_value=0.0,
            max_value=1.0,
            format="percent",
            width="medium",
            help="Signal value as a fraction of its own threshold. Full bar means the signal is at or over its limit.",
        ),
        "state": st.column_config.TextColumn("State", width="small"),
    }


def signal_dataframe(signals: Sequence[dict], *, empty_message: str = "No signals.") -> None:
    """Render one detector's signals with a threshold progress column."""
    frame = signal_table(signals)
    if frame.empty:
        empty_state("No signals", empty_message)
        return
    st.dataframe(frame, width="stretch", hide_index=True, column_config=signal_config())


# --------------------------------------------------------------------------- charts


def prepare_theme() -> None:
    """Ensure the dashboard Altair theme is registered and active."""
    register_altair_theme()


def detector_rate_chart(df: pd.DataFrame, *, title: str = "Detection rate by attack class") -> Any:
    """Grouped bars of detection rate per attack, one bar per detector.

    Expects the long frame from ``web_helpers.detection_rate_frame`` (columns
    ``attack``, ``detector``, ``detection rate``).

    The bars are vertical and grouped on ``xOffset`` deliberately: with a
    continuous ``x``, Vega-Lite keeps the offset for ``mark_bar`` but silently
    drops it for ``mark_text``, which stacks the two value labels on top of each
    other. Grouping on the discrete axis keeps bar and label in step.
    """
    import altair as alt

    value = "detection rate"
    # Order the bars the same way the per-attack table lists them, using an
    # explicit category order. A `sort="-y"` reference would be resolved
    # independently in each layer and the union of the two resolved domains
    # raises "conflicting sort properties"; an explicit order is unambiguous.
    attack_order = list(dict.fromkeys(df["attack"]))

    base = alt.Chart(df).encode(
        x=alt.X("attack:N", title=None, sort=attack_order,
                axis=alt.Axis(labelLimit=200, labelAngle=-25, ticks=False)),
        xOffset=alt.XOffset("detector:N", sort=list(DETECTOR_ORDER)),
        # Headroom above 1.0 so the value label on a full-height bar is not
        # clipped by the top of the plot; the axis still stops at 1.0.
        y=alt.Y(
            f"{value}:Q",
            title="Detection rate",
            scale=alt.Scale(domain=[0, 1.12]),
            axis=alt.Axis(values=[0, 0.2, 0.4, 0.6, 0.8, 1.0]),
        ),
        color=alt.Color("detector:N", sort=list(DETECTOR_ORDER),
                        legend=alt.Legend(title=None, orient="top")),
        tooltip=["attack:N", "detector:N", alt.Tooltip(f"{value}:Q", format=".3f")],
    )
    bars = base.mark_bar(cornerRadius=4)
    labels = base.mark_text(
        dy=-5, align="center", font="JetBrains Mono, monospace", fontSize=10,
    ).encode(text=alt.Text(f"{value}:Q", format=".3f"))
    return (bars + labels).properties(title=title, height=300)


def rate_line_chart(
    df: pd.DataFrame,
    *,
    x: str,
    x_title: str,
    y: str = "detection rate:Q",
    series: str = "detector:N",
    title: str = "",
    threshold: float | None = None,
) -> Any:
    """Line chart for the noise / group sweeps, one line per detector.

    Defaults match the long frames from ``web_helpers.noise_sweep_frame`` and
    ``group_sweep_frame``. If ``threshold`` is given, a dashed reference rule and
    a value label are drawn.
    """
    import altair as alt

    base = alt.Chart(df).properties(title=title)
    # Explicit sort keeps statistical = cyan and pauli = violet instead of
    # following Vega-Lite's alphabetical domain ordering.
    lines = base.encode(
        x=alt.X(x, title=x_title),
        y=alt.Y(y, title="Detection rate", scale=alt.Scale(domain=[0, 1])),
        color=alt.Color(series, sort=list(DETECTOR_ORDER),
                        legend=alt.Legend(title=None, orient="top")),
    ).mark_line(strokeWidth=2.2)

    # The legend is declared once, on the line layer. Omitting it on the point
    # layer (rather than passing legend=None) lets the shared scale resolve to a
    # single legend instead of a conflicting disable flag.
    dots = base.encode(
        x=alt.X(x, title=x_title),
        y=alt.Y(y, title="Detection rate", scale=alt.Scale(domain=[0, 1])),
        color=alt.Color(series, sort=list(DETECTOR_ORDER)),
    ).mark_point(size=34, filled=True, opacity=0.9)

    layers = [lines, dots]
    if threshold is not None and not df.empty:
        rule_data = pd.DataFrame({"t": [threshold], "yn": [1.0], "label": [f"threshold {threshold:.3f}"]})
        layers.append(
            alt.Chart(rule_data).mark_rule(strokeDash=[4, 4], opacity=0.7).encode(
                x=alt.X("t:Q"), y=alt.Y("yn:Q", axis=None, scale=alt.Scale(domain=[0, 1]))
            )
        )
        layers.append(
            alt.Chart(rule_data).mark_text(
                dx=-6, dy=-6, align="right", fontSize=10, fontWeight=600
            ).encode(x=alt.X("t:Q"), y=alt.Y("yn:Q", axis=None), text="label:N")
        )
    return alt.layer(*layers)


__all__ = [
    "badge", "badges", "callout", "detector_rate_chart", "empty_state", "kpi",
    "kpi_row", "page_header", "pipeline", "prepare_theme", "rate_line_chart",
    "section_card", "signal_dataframe", "signal_table", "styled_table",
    "verdict_tone",
]
