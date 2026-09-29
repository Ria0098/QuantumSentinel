"""Tests for signing, distribution, verification and parity checks."""

from __future__ import annotations

import unittest

from qsentinel.channel import QuantumChannel
from qsentinel.config import ExperimentConfig, ProtocolConfig
from qsentinel.protocol.sender import make_transaction, sign
from qsentinel.protocol.state import QDSTransaction, SignatureBlock
from qsentinel.protocol.verifier import (
    amplification_checks,
    parity_groups,
    verify,
    witness_checks,
)


class TestSigning(unittest.TestCase):
    def setUp(self) -> None:
        self.rng = __import__("qsentinel.config", fromlist=["ExperimentConfig"]).ExperimentConfig().rng(4)
        self.config = ExperimentConfig()
        self.txn = make_transaction(self.rng, 8)

    def test_signed_values_follow_xor(self):
        self.assertEqual(
            tuple(self.txn.signed_values),
            tuple(int(m) ^ int(k) for m, k in zip(self.txn.message, self.txn.key)),
        )

    def test_basis_follows_key(self):
        self.assertEqual(
            tuple(self.txn.bases()),
            tuple("Z" if k == "0" else "X" for k in self.txn.key),
        )

    def test_signature_block_holds_one_qubit_per_position(self):
        block = sign(self.txn)
        self.assertIsInstance(block, SignatureBlock)
        self.assertEqual(len(block.qubits), 8)

    def test_transaction_id_is_deterministic(self):
        clone = QDSTransaction(
            message=self.txn.message,
            key=self.txn.key,
            nonce=self.txn.nonce,
            sender_id=self.txn.sender_id,
            verifier_id=self.txn.verifier_id,
            requesting_entity=self.txn.requesting_entity,
        )
        self.assertEqual(self.txn.transaction_id, clone.transaction_id)


class TestParityGroups(unittest.TestCase):
    def test_grouped_consecutively(self):
        self.assertEqual(parity_groups(4, 2), ((0, 1), (2, 3)))

    def test_leftover_copies_dropped_from_groups(self):
        self.assertEqual(parity_groups(5, 2), ((0, 1), (2, 3)))

    def test_singleton_groups_for_size_one(self):
        self.assertEqual(parity_groups(4, 1), tuple((i,) for i in range(4)))


class TestCleanVerification(unittest.TestCase):
    def test_clean_transaction_accepts_for_every_group_size(self):
        for group_size in (1, 2, 3, 4):
            config = ExperimentConfig()
            protocol = ProtocolConfig(parity_group_size=group_size)
            rng = config.rng(100 + group_size)
            txn = make_transaction(rng, 8)
            block = sign(txn)
            channel = QuantumChannel(protocol, config.channel, rng)
            distributed = channel.transmit(block)
            report = verify(distributed, protocol, rng, freshness_ok=True)
            self.assertEqual(report.mismatch_count(), 0, msg=f"group size {group_size}")
            self.assertTrue(report.signature_valid, msg=f"group size {group_size}")
            self.assertTrue(report.accepted, msg=f"group size {group_size}")

    def test_freshness_flag_fails_closed(self):
        config = ExperimentConfig()
        protocol = config.protocol
        rng = config.rng(13)
        txn = make_transaction(rng, 8)
        block = sign(txn)
        distributed = QuantumChannel(protocol, config.channel, rng).transmit(block)
        replay = verify(distributed, protocol, rng, freshness_ok=False)
        self.assertFalse(replay.accepted)
        self.assertIn("nonce replay", replay.reject_reason)
        from qsentinel.detection.engine import build_input
        from qsentinel.detection.statistical import StatisticalDetector
        verdict = StatisticalDetector().analyse(
            build_input(replay, config.detection, frozenset({"alice", "victor"}))
        )
        self.assertIn("replay", verdict.tripped_signals)
        self.assertTrue(verdict.is_threat)


class TestAmplificationCounts(unittest.TestCase):
    def test_parity_group_count_follows_configuration(self):
        for group_size, expected in ((1, 32), (2, 16), (4, 8)):
            config = ExperimentConfig()
            protocol = config.protocol.with_group_size(group_size)
            self.assertEqual(protocol.parity_group_count, expected)

    def test_amplification_checks_emit_one_outcome_per_group(self):
        config = ExperimentConfig()
        protocol = config.protocol
        rng = config.rng(17)
        txn = make_transaction(rng, 8)
        block = sign(txn)
        distributed = QuantumChannel(protocol, config.channel, rng).transmit(block)
        checks, outcomes = amplification_checks(distributed, protocol.parity_group_size, rng)
        self.assertEqual(len(checks), protocol.parity_group_count)
        self.assertEqual(len(outcomes), protocol.parity_group_count)
        self.assertTrue(all(check.passed for check in checks))


class TestWitnessChecks(unittest.TestCase):
    def test_witness_checks_always_pass_on_clean_channel(self):
        config = ExperimentConfig()
        protocol = config.protocol
        rng = config.rng(12)
        txn = make_transaction(rng, 8)
        block = sign(txn)
        distributed = QuantumChannel(protocol, config.channel, rng).transmit(block)
        checks, _ = witness_checks(distributed)
        self.assertTrue(all(check.passed for check in checks))
        self.assertEqual(len(checks), len(distributed.witness_pairs))


if __name__ == "__main__":
    unittest.main()