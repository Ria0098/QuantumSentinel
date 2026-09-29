#!/usr/bin/env python3
"""Evaluate the detectors over a controlled experiment and print the metrics.

Usage:
    python scripts/run_evaluation.py [--trials N] [--output results/evaluation.json]

Equivalent to ``qsentinel evaluate --output ...`` but usable as a plain script.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qsentinel.config import ExperimentConfig
from qsentinel.evaluation import run_evaluation
from qsentinel.reporting.console import heading, table
from qsentinel.reporting.export import write_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=50)
    parser.add_argument("--trials-per-attack", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    config = ExperimentConfig()
    if args.seed is not None:
        config = config.seeded(args.seed)

    trials = args.trials_per_attack or args.trials
    result = run_evaluation(config, trials_per_attack=trials)
    summary = result.summary()

    if args.output:
        write_json(args.output, summary)
        print(f"wrote {args.output}")

    print(heading("Detection evaluation"))
    print()
    rows = []
    for detector in ("statistical", "pauli_measurement"):
        entry = summary[detector]
        ci = entry["detection_rate_ci95"]
        rows.append(
            [
                detector,
                f"{entry['detection_rate']:.3f}",
                f"[{ci[0]:.3f},{ci[1]:.3f}]",
                f"{entry['false_alarm_rate']:.3f}",
                f"{entry['accuracy']:.3f}",
            ]
        )
    print(
        table(
            ["detector", "detection", "95% CI", "false alarm", "accuracy"],
            rows,
            ["left", "right", "left", "right", "right"],
        )
    )


if __name__ == "__main__":
    main()