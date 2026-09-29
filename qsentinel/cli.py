"""Interactive command-line interface.

``python -m qsentinel.cli`` (or the ``qsentinel-demo`` script) exposes the full
prototype:

    qsentinel scenarios
        run all six attack scenarios once and print a comparison table
    qsentinel demo [scenario]
        run one scenario with full detail, or step through them interactively
    qsentinel evaluate [--trials N] [--output PATH]
        controlled experiment aggregating confusion-matrix metrics
    qsentinel noise-sweep [--rates 0 0.005 0.01 ...] [--output PATH]
        detector behaviour as a function of channel decoherence
    qsentinel group-sweep [--sizes 1 2 ...] [--output PATH]
        detector behaviour as a function of distillation group size
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from . import __version__
from .attacks import ATTACK_BENIGN, ATTACK_ORDER
from .config import ExperimentConfig, presets
from .evaluation import run_evaluation, run_group_size_sweep, run_noise_sweep
from .reporting import (
    render_comparison,
    render_evaluation,
    render_scenario,
    scenario_as_dict,
)
from .session import QDSSession
from .reporting.export import write_json
from .reporting.console import rule

DEFAULT_TRIALS = 50


def _parse_trials_safe(parser: argparse.ArgumentParser, seed: str, upper: int) -> int:
    if not seed.isdigit():
        raise parser.error(f"expected a positive integer, got {seed!r}")
    value = int(seed)
    if not 1 <= value <= upper:
        raise parser.error(f"value must be within 1 and {upper}")
    return value


def _parse_float_list(text: str) -> list[float]:
    return [float(token) for token in re.split(r"[,\s]+", text.strip()) if token]


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--seed", type=int, default=None, help="override the protocol seed"
    )
    parser.add_argument(
        "--preset",
        choices=tuple(presets),
        default=None,
        help="named configuration preset",
    )


def _output_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="write the JSON export to this path instead of printing it",
    )


def _config(args: argparse.Namespace) -> ExperimentConfig:
    if args.preset:
        return presets[args.preset]
    config = ExperimentConfig()
    if args.seed is not None:
        config = config.seeded(args.seed)
    return config


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise SystemExit(f"error: {message}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qsentinel",
        description="QuantumSigGuard - quantum-inspired cyber threat detection "
        "for teleportation-based QDS, SIH26141",
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    scenarios = subparsers.add_parser("scenarios", help="run all six scenarios once")
    _common(scenarios)
    scenarios.add_argument(
        "--json", action="store_true", help="print JSON instead of the table"
    )

    demo = subparsers.add_parser("demo", help="run one scenario in full detail")
    _common(demo)
    demo.add_argument(
        "scenario",
        nargs="?",
        default=None,
        help=f"one of {', '.join(ATTACK_ORDER)} (default: step through all)",
    )

    evaluate = subparsers.add_parser(
        "evaluate", help="controlled experiment with metrics"
    )
    _common(evaluate)
    evaluate.add_argument(
        "--trials", type=int, default=DEFAULT_TRIALS, help=f"trials per attack (default {DEFAULT_TRIALS})"
    )
    _output_option(evaluate)

    sweep = subparsers.add_parser("noise-sweep", help="sweep channel decoherence")
    _common(sweep)
    sweep.add_argument(
        "--rates",
        default="0.000 0.002 0.005 0.010 0.020",
        help="whitespace/comma separated decoherence rates",
    )
    sweep.add_argument("--trials", type=int, default=50)
    _output_option(sweep)

    group = subparsers.add_parser(
        "group-sweep", help="sweep the distillation group size"
    )
    _common(group)
    group.add_argument(
        "--sizes",
        default="1 2 3 4",
        help="whitespace/comma separated parity group sizes",
    )
    group.add_argument("--trials", type=int, default=50)
    _output_option(group)

    return parser


def command_scenarios(args: argparse.Namespace) -> int:
    config = _config(args)
    session = QDSSession(config)
    results = session.run_all()
    if args.json:
        print(json.dumps([scenario_as_dict(r) for r in results], indent=2))
    else:
        print(render_comparison(results))
    return 0


def command_demo(args: argparse.Namespace) -> int:
    config = _config(args)
    session = QDSSession(config)
    selection = [args.scenario] if args.scenario else list(ATTACK_ORDER)
    for attack_key in selection:
        if attack_key == ATTACK_BENIGN:
            session.run_scenario(ATTACK_BENIGN)
        result = session.run_scenario(attack_key)
        print(render_scenario(result))
        print()
    return 0


def command_evaluate(args: argparse.Namespace) -> int:
    trials = _parse_trials_safe(args, str(args.trials), 10000)
    config = _config(args)
    result = run_evaluation(config, trials)
    summary = result.summary()
    if args.output:
        write_json(args.output, summary)
        print(f"wrote {args.output}")
    else:
        print(render_evaluation(summary))
    return 0


def command_noise_sweep(args: argparse.Namespace) -> int:
    config = _config(args)
    rates = _parse_float_list(args.rates)
    rows = run_noise_sweep(rates, config, args.trials)
    payload = {"label": "noise_sweep", "decoherence_rates": rows}
    if args.output:
        write_json(args.output, payload)
        print(f"wrote {args.output}")
        return 0
    print(render_evaluation_table(rows, "decoherence", "decoherence_rate"))
    return 0


def command_group_sweep(args: argparse.Namespace) -> int:
    config = _config(args)
    sizes = [int(token) for token in _parse_float_list(args.sizes)]
    if not sizes or any(size < 1 for size in sizes):
        raise SystemExit("error: group sizes must be positive integers")
    rows = run_group_size_sweep(sizes, config, args.trials)
    payload = {"label": "group_size_sweep", "parity_group_sizes": rows}
    if args.output:
        write_json(args.output, payload)
        print(f"wrote {args.output}")
        return 0
    print(render_evaluation_table(rows, "group size", "parity_group_size"))
    return 0


def render_evaluation_table(rows: list[dict[str, Any]], label: str, key: str) -> str:
    """Render a sweep result as a table with detection and false-alarm columns."""
    from .reporting.console import heading, table

    headers = [
        label,
        "statistical detection",
        "statistical false alarm",
        "pauli detection",
        "pauli false alarm",
        "mean E",
        "runtime",
    ]
    return "\n".join(
        [
            heading(f"{label} sweep"),
            table(
                headers,
                [
                    [
                        f"{row[key]}",
                        f"{row['statistical_detection_rate']:.3f}",
                        f"{row['statistical_false_alarm_rate']:.3f}",
                        f"{row['pauli_detection_rate']:.3f}",
                        f"{row.get('pauli_false_alarm_rate', 0.0):.3f}",
                        f"{row.get('mean_mismatch_rate', 0.0):.4f}",
                        f"{row.get('mean_runtime_seconds', 0.0) * 1000:.1f} ms",
                    ]
                    for row in rows
                ],
                ["right", "right", "right", "right", "right", "right", "right"],
            ),
            rule(),
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        handlers = {
            "scenarios": command_scenarios,
            "demo": command_demo,
            "evaluate": command_evaluate,
            "noise-sweep": command_noise_sweep,
            "group-sweep": command_group_sweep,
        }
        return handlers[args.command](args)
    except KeyboardInterrupt:
        print()
        return 130


if __name__ == "__main__":
    raise SystemExit(main())