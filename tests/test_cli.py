"""Tests for the interactive CLI and the reporting/export path."""

from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from qsentinel.session import QDSSession
from qsentinel.reporting import render_scenario, scenario_as_dict
from qsentinel.reporting.export import write_json


def _run_cli(*argv: str) -> tuple[int, str]:
    from qsentinel.cli import main

    captured = StringIO()
    try:
        with redirect_stdout(captured):
            code = main(list(argv))
    except SystemExit as exc:  # argparse --help/--version
        code = exc.code or 0
        captured.write("")
    return code, captured.getvalue()


class TestScenarioExports(unittest.TestCase):
    def setUp(self) -> None:
        self.session = QDSSession()

    def test_scenario_as_dict_round_trip(self):
        result = self.session.run_scenario("legitimate")
        payload = json.loads(json.dumps(scenario_as_dict(result)))
        self.assertEqual(payload["scenario"], "legitimate")
        self.assertIn("detection_measures", payload)
        self.assertIn("verification", payload)

    def test_write_json_pretty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "report.json"
            write_json(path, {"a": 1})
            self.assertTrue(path.exists())
            self.assertEqual(json.loads(path.read_text()), {"a": 1})

    def test_render_scenario_not_empty(self):
        text = render_scenario(self.session.run_scenario("forgery"))
        self.assertIn("Scenario", text)
        self.assertIn("THREAT", text)


class TestCliSubcommands(unittest.TestCase):
    def test_scenarios_subcommand(self):
        code, out = _run_cli("scenarios")
        self.assertEqual(code, 0)
        self.assertIn("legitimate", out)
        self.assertIn("channel_manipulation", out)

    def test_demo_for_one_scenario(self):
        code, out = _run_cli("demo", "forgery")
        self.assertEqual(code, 0)
        self.assertIn("Signature forgery", out)

    def test_evaluate_subcommand(self):
        code, out = _run_cli("evaluate", "--trials", "5")
        self.assertEqual(code, 0)
        self.assertIn("Evaluation summary", out)

    def test_noise_sweep_subcommand(self):
        code, out = _run_cli("noise-sweep", "--trials", "5")
        self.assertEqual(code, 0)
        self.assertIn("decoherence", out)

    def test_unknown_scenario_is_an_error(self):
        from qsentinel.cli import main
        with self.assertRaises(KeyError):
            main(["demo", "not_a_scenario"])

    def test_version_flag(self):
        code, out = _run_cli("--version")
        self.assertEqual(code, 0)
        self.assertIn("1.0.0", out)


if __name__ == "__main__":
    unittest.main()