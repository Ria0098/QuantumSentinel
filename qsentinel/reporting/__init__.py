"""Reporting: console rendering and JSON/Markdown export."""

from .console import bar, bold, colour, heading, rule, table, verdict_label
from .export import scenario_as_dict, scenario_to_markdown, write_json
from .render import (
    render_comparison,
    render_evaluation,
    render_scenario,
)

__all__ = [
    "bar",
    "bold",
    "colour",
    "heading",
    "render_comparison",
    "render_evaluation",
    "render_scenario",
    "rule",
    "scenario_as_dict",
    "scenario_to_markdown",
    "table",
    "verdict_label",
    "write_json",
]