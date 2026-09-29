"""End-to-end tests for the session orchestrator and the controlled evaluation."""

from __future__ import annotations

import unittest

import numpy as np

from qsentinel.attacks import ATTACK_ORDER
from qsentinel.config import ExperimentConfig, ChannelConfig
from qsentinel.channel import QuantumChannel
from qsentinel.evaluation import run_evaluation
from qsentinel.evaluation.metrics import (
    ConfusionMatrix,
    confusion_from_labels,
    wilson_interval,
)
from qsentinel.protocol.sender import make_transaction, sign
from qsentinel.protocol.verifier import verify
from qsentinel.session import QDSSession


class TestMetrics(unittest.TestCase):
    def test_confusion_counts(self):
        matrix = confusion_from_labels([True, True, False, False], [True, False, True, False])
        self.assertEqual((matrix.true_positives, matrix.false_negatives,
                          matrix.false_positives, matrix.true_negatives), (1, 1, 1, 1))

    def test_detection_rate(self):
        matrix = ConfusionMatrix(true_positives=8, false_negatives=2)
        self.assertAlmostEqual(matrix.detection_rate, 0.8)

    def test_false_alarm_rate(self):
        matrix = ConfusionMatrix(false_positives=1, true_negatives=99)
        self.assertAlmostEqual(matrix.false_alarm_rate, 0.01)

    def test_accuracy(self):
        matrix = ConfusionMatrix(true_positives=9, true_negatives=8, false_positives=1, false_negatives=2)
        self.assertAlmostEqual(matrix.accuracy, 17 / 20)

    def test_wilson_interval_is_empty_on_zero_trials(self):
        self.assertEqual(wilson_interval(0, 0), (0.0, 0.0))

    def test_wilson_reasonable_for_deduction(self):
        lower, upper = wilson_interval(100, 100)
        self.assertGreater(lower, 0.95)
        self.assertLessEqual(upper, 1.0)

    def test_add_accumulates(self):
        a = ConfusionMatrix(1, 2, 3, 4)
        b = ConfusionMatrix(5, 6, 7, 8)
        added = a.add(b)
        self.assertEqual((added.true_positives, added.false_positives,
                          added.true_negatives, added.false_negatives), (6, 8, 10, 12))


class TestControlledEvaluation(unittest.TestCase):
    def test_run_evaluation_shapes(self):
        result = run_evaluation(trials_per_attack=8)
        self.assertEqual(len(result.trials), 8 * len(ATTACK_ORDER))
        summary = result.summary()
        self.assertEqual(summary["total_trials"], 8 * len(ATTACK_ORDER))
        self.assertIn("per_attack", summary)
        self.assertEqual(len(summary["per_attack"]), len(ATTACK_ORDER))

    def test_attack_rows_exist_for_every_attack(self):
        result = run_evaluation(trials_per_attack=4)
        attacks_in_rows = {row["attack"] for row in result.attack_rows()}
        self.assertEqual(attacks_in_rows, set(ATTACK_ORDER))

    def test_noise_degrades_legitimate_acceptance(self):
        config = ExperimentConfig(channel=ChannelConfig(decoherence_rate=0.05))
        session = QDSSession(config)
        rejects = sum(
            1
            for _ in range(30)
            if not session.run_scenario("legitimate").accepted_by_protocol
        )
        # With 5% per-copy decoherence, most transactions are rejected by the protocol.
        self.assertGreater(rejects, 10)


class TestNoiseModelStatistics(unittest.TestCase):
    def test_loss_drops_qubits(self):
        config = ExperimentConfig(channel=ChannelConfig(loss_rate=1.0))
        protocol = config.protocol
        rng = config.rng(33)
        txn = make_transaction(rng, 8)
        block = sign(txn)
        distributed = QuantumChannel(protocol, config.channel, rng).transmit(block)
        self.assertEqual(distributed.dropped_qubits, protocol.test_qubit_count)
        self.assertEqual(len(distributed.test_qubits), 0)

    def test_full_decoherence_corrupts_some_qubits(self):
        config = ExperimentConfig(channel=ChannelConfig(decoherence_rate=1.0))
        protocol = config.protocol
        rng = config.rng(34)
        txn = make_transaction(rng, 8)
        block = sign(txn)
        distributed = QuantumChannel(protocol, config.channel, rng).transmit(block)
        self.assertGreater(distributed.residual_errors().get("I", 0), 0)

    def test_errored_copies_are_marked(self):
        config = ExperimentConfig(channel=ChannelConfig(decoherence_rate=0.05))
        protocol = config.protocol
        rng = config.rng(35)
        txn = make_transaction(rng, 8)
        distributed = QuantumChannel(protocol, config.channel, rng).transmit(sign(txn))
        errored = sum(1 for q in distributed.test_qubits if q.is_errored)
        self.assertGreater(errored, 0)


class TestSessionLifecycle(unittest.TestCase):
    def test_accepted_history_grows_only_on_accept(self):
        config = ExperimentConfig()
        session = QDSSession(config)
        session.run_scenario("legitimate")
        self.assertEqual(len(session.accepted_history), 1)
        session.run_scenario("forgery")
        self.assertEqual(len(session.accepted_history), 1)

    def test_replay_cache_remembers_only_accepted(self):
        config = ExperimentConfig()
        session = QDSSession(config)
        legit_result = session.run_scenario("legitimate")
        self.assertFalse(session.replay_cache.is_fresh(legit_result.outcome.transaction))
        attack_result = session.run_scenario("forgery")
        self.assertTrue(session.replay_cache.is_fresh(attack_result.outcome.transaction))

    def test_rng_stream_decorrelates(self):
        config = ExperimentConfig()
        a = config.rng(0).integers(0, 2, size=4)
        b = config.rng(1).integers(0, 2, size=4)
        self.assertFalse(np.array_equal(a, b))

    def test_reset_clears_state(self):
        config = ExperimentConfig()
        session = QDSSession(config)
        session.run_scenario("legitimate")
        session.reset()
        self.assertEqual(session.accepted_history, ())
        self.assertEqual(len(session.replay_cache), 0)


if __name__ == "__main__":
    unittest.main()