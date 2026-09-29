#!/usr/bin/env python3
"""Benchmark the wall-clock runtime of the end-to-end pipeline.

Runs a configurable number of repetitions and reports the mean per-scenario
runtime (signing + distribution + verification + detection) so the report can
quote prototype performance numbers.
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qsentinel.attacks import ATTACK_BENIGN, ATTACK_ORDER, ATTACK_REPLAY
from qsentinel.config import ExperimentConfig
from qsentinel.session import QDSSession


def mean(values: list[float]) -> float:
    return statistics.mean(values) if values else 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=30)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    config = ExperimentConfig()
    if args.seed is not None:
        config = config.seeded(args.seed)

    session = QDSSession(config)
    timings: dict[str, list[float]] = {key: [] for key in ATTACK_ORDER}

    for _ in range(args.trials):
        session.reset()
        for attack in ATTACK_ORDER:
            if attack == ATTACK_REPLAY:
                session.run_scenario(ATTACK_BENIGN)
            timings[attack].append(session.run_scenario(attack).elapsed_seconds)

    total_runs = args.trials * len(ATTACK_ORDER)
    all_values = [value for values in timings.values() for value in values]

    print(f"mean wall-clock runtime over {args.trials} repetitions per scenario")
    print(f"{'scenario':<28} {'mean ms':>9}   {'min ms':>8}   {'max ms':>8}")
    for attack in ATTACK_ORDER:
        values = timings[attack]
        print(
            f"{attack:<28} {mean(values) * 1000:9.2f}   "
            f"{min(values) * 1000:8.2f}   {max(values) * 1000:8.2f}"
        )
    print("-" * 60)
    print(
        f"{'OVERALL':<28} {mean(all_values) * 1000:9.2f}   "
        f"({total_runs} transactions)"
    )


if __name__ == "__main__":
    main()