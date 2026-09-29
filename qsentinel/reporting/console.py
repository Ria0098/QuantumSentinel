"""Terminal formatting helpers.

Kept free of business logic so the reporting style can change without touching
the protocol, attack or detection layers.
"""

from __future__ import annotations

import os
import shutil
import sys
from typing import Iterable, Sequence

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"

_COLOURS = {
    "threat": RED,
    "legitimate": GREEN,
    "warn": YELLOW,
    "info": BLUE,
    "accent": MAGENTA,
    "muted": DIM,
}


def _supports_colour() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return sys.stdout.isatty()


def colour(text: str, style: str) -> str:
    """Wrap ``text`` in an ANSI style, or return it unchanged when unsupported."""
    if not _supports_colour():
        return text
    code = _COLOURS.get(style)
    return f"{code}{text}{RESET}" if code else text


def bold(text: str) -> str:
    """Render ``text`` in bold when the terminal supports it."""
    return f"{BOLD}{text}{RESET}" if _supports_colour() else text


def heading(text: str, width: int = 78) -> str:
    """Return an underlined section heading."""
    return f"{bold(text)}\n{colour('-' * min(width, len(text) + 8), 'muted')}"


def rule(char: str = "-", width: int = 78) -> str:
    """Return a horizontal rule."""
    return colour(char * width, "muted")


def table(
    headers: Sequence[str],
    rows: Iterable[Sequence[object]],
    aligns: Sequence[str] | None = None,
) -> str:
    """Render a simple fixed-width table."""
    materialised = [[str(cell) for cell in row] for row in rows]
    if not materialised:
        return "(no rows)"
    widths = [len(str(header)) for header in headers]
    for row in materialised:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))
    alignment = list(aligns or ["left"] * len(headers))
    alignment += ["left"] * (len(widths) - len(alignment))

    def render(cells: Sequence[str], bold_row: bool = False) -> str:
        parts = []
        for index, cell in enumerate(cells):
            if alignment[index] == "right":
                parts.append(cell.rjust(widths[index]))
            else:
                parts.append(cell.ljust(widths[index]))
        line = "  ".join(parts).rstrip()
        return bold(line) if bold_row else line

    out = [render([str(h) for h in headers], bold_row=True), "  ".join("-" * w for w in widths)]
    out.extend(render(row) for row in materialised)
    return "\n".join(out)


def verdict_label(is_threat: bool) -> str:
    """Return a colourised THREAT / LEGITIMATE label."""
    return (
        colour("THREAT", "threat") if is_threat else colour("LEGITIMATE", "legitimate")
    )


def bar(fraction: float, width: int = 20) -> str:
    """Render a fraction as a filled bar."""
    fraction = min(1.0, max(0.0, fraction))
    filled = int(round(fraction * width))
    return "#" * filled + "." * (width - filled)


def terminal_width(default: int = 100) -> int:
    """Best-effort terminal width."""
    try:
        return shutil.get_terminal_size((default, 24)).columns
    except OSError:
        return default
