#!/usr/bin/env python3
"""Produce the complete `results/` bundle for the Word report.

Writes:
    results/config.json             resolved configuration used for the run
    results/scenarios.json          one JSON object per attack scenario
    results/scenarios.md            per-scenario markdown sections
    results/evaluation.json         confusion-matrix metrics over every scenario
    results/noise_sweep.json        detector behaviour vs decoherence
    results/group_sweep.json        detector behaviour vs distillation group size
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qsentinel.attacks import ATTACK_BENIGN, ATTACK_ORDER
from qsentinel.config import ExperimentConfig
from qsentinel.evaluation import (
    run_evaluation,
    run_group_size_sweep,
    run_noise_sweep,
)
from qsentinel.reporting.export import scenario_as_dict, write_json
from qsentinel.session import QDSSession

NOISE_RATES = (0.000, 0.002, 0.005, 0.010, 0.020, 0.050)
GROUP_SIZES = (1, 2, 3, 4)


def generate_scenarios(config: ExperimentConfig) -> list[dict]:
    session = QDSSession(config)
    payloads = []
    for attack in ATTACK_ORDER:
        if attack == ATTACK_BENIGN:
            session.run_scenario(ATTACK_BENIGN)
        result = session.run_scenario(attack)
        payloads.append(scenario_as_dict(result))
    return payloads


def generate_markdown(config: ExperimentConfig) -> str:
    from qsentinel.reporting.export import scenario_to_markdown

    session = QDSSession(config)
    blocks = [
        "# Scenario report\n",
        f"Produced with seed `{config.seed}`.\n",
    ]
    for attack in ATTACK_ORDER:
        if attack == ATTACK_BENIGN:
            session.run_scenario(ATTACK_BENIGN)
        result = session.run_scenario(attack)
        blocks.append(scenario_to_markdown(result))
    return "\n".join(blocks)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=200, help="trials per attack in the evaluation")
    parser.add_argument("--sweep-trials", type=int, default=40, help="trials per point in the sweeps")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--output", type=Path, default=Path("results"))
    parser.add_argument("--noise-rates", default=None, help="comma separated decoherence rates")
    args = parser.parse_args()

    config = ExperimentConfig()
    if args.seed is not None:
        config = config.seeded(args.seed)

    output: Path = args.output
    output.mkdir(parents=True, exist_ok=True)

    print("generating scenarios...")
    scenarios = generate_scenarios(config)
    markdown = generate_markdown(config)
    write_json(output / "config.json", config.describe())
    write_json(output / "scenarios.json", scenarios)
    (output / "scenarios.md").write_text(markdown, encoding="utf-8")

    print(f"running evaluation with {args.trials} trials per attack...")
    evaluation = run_evaluation(config, trials_per_attack=args.trials).summary()
    write_json(output / "evaluation.json", evaluation)

    print("running noise sweep...")
    rates = (
        tuple(float(x) for x in args.noise_rates.split(","))
        if args.noise_rates
        else NOISE_RATES
    )
    noise = run_noise_sweep(rates, config, trials_per_attack=args.sweep_trials)
    write_json(output / "noise_sweep.json", {"decoherence_rates": noise})

    print("running group-size sweep...")
    group = run_group_size_sweep(
        GROUP_SIZES,
        config,
        trials_per_attack=args.sweep_trials,
    )
    write_json(output / "group_sweep.json", {"parity_group_sizes": group})

    print(f"done. artifacts written to {output}/")


if __name__ == "__main__":
    main()