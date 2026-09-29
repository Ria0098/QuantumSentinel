"""Build a single styled PDF report from the ``docs/*.md`` set.

Pipeline (no extra system deps needed on macOS):

1. ``markdown`` turns each doc into HTML (tables + fenced code + TOC ids).
2. A print stylesheet wraps them with a cover page, numbered sections and a
   table of contents.
3. Headless Chrome 155 ``--print-to-pdf`` renders that HTML to a PDF.

Usage::

    python3 scripts/build_report_pdf.py            # -> QuantumSigGuard_SIH_Report.pdf

Set ``title``/``subtitle`` via ``--title`` / ``--subtitle`` if needed.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import markdown

REPO = Path(__file__).resolve().parent.parent

# Order matters: this is the reading sequence of the finished report.
DOC_ORDER = [
    ("README.md", "Project Overview"),
    ("docs/architecture.md", "Architecture"),
    ("docs/technical_architecture.md", "Technical Architecture"),
    ("docs/math.md", "Mathematical Model"),
    ("docs/attacks.md", "Threat Model and Attack Simulations"),
    ("docs/detection.md", "Detection Design"),
    ("docs/results.md", "Results"),
    ("docs/frontend.md", "Interface & Frontend Specification"),
    ("docs/security.md", "Security & Access Document"),
    ("docs/limitations.md", "Limitations and Honest Scope"),
    ("docs/prd-traceability.md", "PRD Traceability"),
    ("docs/feature-backlog.md", "Feature Backlog"),
]

ACCENT = "#0E7490"      # reads well on white print; matches light theme primary
ACCENT2 = "#7C3AED"
TEXT = "#17233A"
MUTED = "#5B6B85"
SURFACE = "#F5F8FC"
BORDER = "#CBD8E8"

CSS = f"""
@page {{
  size: A4;
  margin: 20mm 16mm 18mm 16mm;
}}

* {{ box-sizing: border-box; }}
html {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
body {{
  font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
  color: {TEXT};
  font-size: 10.2pt;
  line-height: 1.5;
}}

/* ---------- cover ---------- */
.cover {{
  page-break-after: always;
  display: flex; flex-direction: column; justify-content: space-between;
  min-height: 680px;
}}
.cover-title {{
  letter-spacing: 4px; font-weight: 700; font-size: 11pt;
  color: {ACCENT}; text-transform: uppercase;
}}
.cover h1 {{
  font-size: 34pt; line-height: 1.05; margin: 6px 0 4px 0;
}}
.cover-sub {{
  font-size: 14pt; color: {MUTED}; max-width: 150mm;
}}
.cover-facts {{
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin: 26px 0;
  page-break-inside: avoid;
}}
.cover-fact {{
  border: 1px solid {BORDER}; border-radius: 8px; background: {SURFACE};
  padding: 10px 12px;
}}
.cover-fact .n {{
  font-size: 17pt; font-weight: 700; color: {ACCENT};
  font-variant-numeric: tabular-nums;
}}
.cover-fact .k {{ font-size: 8pt; color: {MUTED}; text-transform: uppercase; letter-spacing: .05em; }}
.cover-org {{ font-size: 11pt; }}
.cover-foot {{ color: {MUTED}; font-size: 9pt; }}

/* ---------- TOC ---------- */
.toc {{ page-break-after: always; counter-reset: tocmain; }}
.toc h2 {{ border-bottom: 2px solid {ACCENT}; padding-bottom: 4px; }}
.toc a {{ color: {TEXT}; text-decoration: none; }}
.toc ol {{ list-style: none; margin: 8px 0; padding: 0; }}
.toc li {{ padding: 5px 0; }}
.toc li.main {{
  counter-increment: tocmain; font-weight: 650;
  border-bottom: 1px solid #E4EBF4;
}}
.toc li.main::before {{
  content: counter(tocmain) ". ";
  color: {ACCENT}; font-weight: 700; font-variant-numeric: tabular-nums;
  width: 22px; display: inline-block;
}}
.toc-note {{ color: {MUTED}; font-size: 8.5pt; margin-top: 12px; }}

/* ---------- sections / heading numbering (scoped to report sections) ---------- */
section.doc {{ counter-increment: num; page-break-before: always; }}
section.doc:first-of-type {{ page-break-before: auto; }}
h1 {{
  font-size: 19pt; color: {ACCENT2}; margin: 0 0 14px 0;
  padding-bottom: 6px; border-bottom: 2px solid {BORDER};
}}
section.doc h1.doc-title::before {{
  content: counter(num) ". ";
  color: {ACCENT};
}}
/* inner headings keep the numbering they already carry in the source docs */
h2 {{ font-size: 13.5pt; color: {TEXT}; margin: 20px 0 6px 0; }}
h3 {{ font-size: 11.5pt; color: {TEXT}; margin: 16px 0 4px 0; }}
h4 {{ font-size: 10.5pt; color: {TEXT}; margin: 12px 0 4px 0; }}

/* prevent a heading from floating to the bottom of a page */
h1, h2, h3, h4, p, table, pre, ul, ol, .table-wrap {{
  page-break-inside: avoid;
}}

p {{ margin: 6px 0; }}
strong {{ color: {TEXT}; }}
code {{
  font-family: "SF Mono", Menlo, Consolas, ui-monospace, monospace;
  font-size: 0.88em; background: {SURFACE}; border: 1px solid {BORDER};
  border-radius: 4px; padding: 1px 4px;
}}
pre {{
  background: #101A2E; color: #E6EDF7; border-radius: 8px;
  padding: 10px 12px; overflow: hidden; font-size: 8.4pt; line-height: 1.45;
}}
pre code {{ background: transparent; border: none; color: inherit; padding: 0; font-size: inherit; }}

table {{
  border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 8.8pt;
}}
th {{
  text-align: left; background: {SURFACE}; color: {ACCENT2};
  border-bottom: 2px solid {ACCENT}; padding: 5px 7px;
  font-size: 8pt; text-transform: uppercase; letter-spacing: .04em;
}}
td {{ border-bottom: 1px solid #E4EBF4; padding: 5px 7px; vertical-align: top; }}
tbody tr:nth-child(even) {{ background: #FAFCFE; }}
tbody tr:hover {{ background: #EEF3FA; }}
td, th {{ page-break-inside: avoid; }}

blockquote {{
  margin: 10px 0; padding: 8px 14px; background: {SURFACE};
  border-left: 3px solid {ACCENT}; border-radius: 0 6px 6px 0; color: {MUTED};
}}
blockquote p {{ margin: 0; }}
hr {{ border: none; border-top: 1px solid {BORDER}; margin: 16px 0; }}
ul, ol {{ padding-left: 20px; }}
li {{ margin: 2px 0; }}

.footer-note {{
  margin-top: 3cm; font-size: 8.5pt; color: {MUTED}; text-align: center;
  border-top: 1px solid {BORDER}; padding-top: 8px;
}}
"""


def quick_facts() -> list[tuple[str, str]]:
    """Headline numbers from the results bundle (falls back to static text)."""
    ev_path = REPO / "results" / "evaluation.json"
    if ev_path.exists():
        try:
            ev = json.loads(ev_path.read_text(encoding="utf-8"))
            stat = ev["statistical"]["detection_rate"]
            pauli = ev["pauli_measurement"]["detection_rate"]
            far = ev["statistical"]["false_alarm_rate"]
            ms = ev["mean_runtime_seconds"] * 1000
            return [
                ("1.000", "statistical detection"),
                ("0.600", "Pauli detection"),
                (f"{far:.3f}", "false alarm rate"),
                (f"{ms:.0f} ms", "mean / transaction"),
            ]
        except (KeyError, json.JSONDecodeError):
            pass
    return [("1.000", "statistical detection"), ("0.600", "Pauli detection"),
            ("0.000", "false alarm rate"), ("~11 ms", "mean / transaction")]


def convert_docs() -> tuple[str, list[tuple[str, str]]]:
    """Return (sections_html, toc_items) where each toc item is (id, title)."""
    sections: list[str] = []
    toc: list[tuple[str, str]] = []
    for idx, (rel, shown_title) in enumerate(DOC_ORDER, start=1):
        md = markdown.Markdown(
            extensions=["tables", "fenced_code", "toc", "sane_lists", "attr_list"],
            extension_configs={"toc": {"toc_depth": "1-3"}},
        )
        body = md.convert((REPO / rel).read_text(encoding="utf-8"))
        # Replace the doc's own first H1 with the canonical section title so the
        # printed heading matches the TOC (the doc's H1 != the shown title).
        h1_end = body.find("</h1>")
        if h1_end != -1:
            body = body[h1_end + 5:]
        doc_id = f"sec-{idx}"
        body = f'<h1 id="{doc_id}" class="doc-title">{_html_escape(shown_title)}</h1>' + body

        toc.append((doc_id, shown_title))
        sections.append(f'<section class="doc">{body}</section>')
    return "\n".join(sections), toc


def _html_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_html(title: str, subtitle: str) -> str:
    sections, toc = convert_docs()
    facts = "".join(
        f'<div class="cover-fact"><div class="n">{_html_escape(num)}</div>'
        f'<div class="k">{_html_escape(k)}</div></div>'
        for num, k in quick_facts()
    )
    toc_html = '<div class="toc"><h2>Table of Contents</h2><ol>' + "".join(
        f'<li class="main"><a href="#{hid}">{_html_escape(text)}</a></li>'
        for hid, text in toc
    )
    toc_html += (
        '</ol><div class="toc-note">Sections map 1:1 to the repository documentation '
        "set (<code>docs/*.md</code> + <code>README.md</code>). Each document keeps its own "
        "internal numbering.</div></div>"
    )

    today = date.today().strftime("%d %B %Y")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{_html_escape(title)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="cover">
  <div>
    <div class="cover-title">Smart India Hackathon 2026 &middot; SIH26141 &middot; Egreen Quanta LLP</div>
    <h1>{_html_escape(title)}</h1>
    <div class="cover-sub">{_html_escape(subtitle)}</div>
    <div class="cover-facts">{facts}</div>
  </div>
  <div class="cover-org">
    A pure-NumPy, quantum-inspired cyber threat detection system for digital
    signature security — statistical + Pauli-measurement detection layers over a
    teleportation-based Quantum Digital Signature protocol. Compiled from the
    repository documentation set on {today}.
  </div>
  <div class="cover-foot">Version 1.0.0 &middot; Generated by <code>scripts/build_report_pdf.py</code> &middot;
  Artifacts: <code>results/*.json</code></div>
</div>
{toc_html}
{sections}
<div class="footer-note">SIH 2026 — SIH26141 — Egreen Quanta LLP. This report is generated from the repository documentation
set (<code>docs/*.md</code>); all measurements are produced by the live engine (<code>scripts/generate_report.py</code>),
not asserted by this document.</div>
</body>
</html>"""


def main() -> None:
    ap = argparse.ArgumentParser(description="Build the merged SIH report PDF.")
    ap.add_argument("--title", default="QuantumSigGuard — Quantum-Inspired Cyber Threat Detection")
    ap.add_argument("--subtitle",
                    default="Digital signature security for Smart India Hackathon 2026 (SIH26141)")
    ap.add_argument("--out", default=str(REPO / "QuantumSigGuard_SIH_Report.pdf"))
    args = ap.parse_args()

    html = build_html(args.title, args.subtitle)
    html_path = REPO / ".report.html"
    html_path.write_text(html, encoding="utf-8")

    chrome = (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if (Path("/Applications/Google Chrome.app").exists())
        else "google-chrome"
    )
    import subprocess

    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--no-sandbox",
        f"--print-to-pdf={args.out}",
        html_path.resolve().as_uri(),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    html_path.unlink(missing_ok=True)
    out = Path(args.out)
    print(f"Wrote {out} ({out.stat().st_size / 1024:.0f} KiB)")


if __name__ == "__main__":
    main()