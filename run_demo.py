#!/usr/bin/env python3
"""One-command demo of QuantumSigGuard.

Runs all six scenarios, prints the method-comparison table and a detailed
report, then runs a short controlled evaluation.  Use ``python run_demo.py``.
"""

from __future__ import annotations

from qsentinel.config import ExperimentConfig
from qsentinel.evaluation import run_evaluation
from qsentinel.reporting import (
    render_comparison,
    render_evaluation,
    render_scenario,
)
from qsentinel.reporting.console import heading, rule
from qsentinel.session import QDSSession


def main() -> None:
    config = ExperimentConfig()
    session = QDSSession(config)

    print(render_comparison(session.run_all()))
    print()
    print(render_scenario(session.run_scenario("channel_manipulation")))
    print()
    print(render_evaluation(run_evaluation(config, trials_per_attack=40).summary()))


if __name__ == "__main__":
    main()