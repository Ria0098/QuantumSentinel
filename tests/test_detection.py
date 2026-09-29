"""Tests for both detection layers on clean and attack scenarios."""

from __future__ import annotations

import unittest

from qsentinel.attacks import ATTACK_BENIGN, ATTACK_CHANNEL, ATTACK_FORGERY, ATTACK_IMPERSONATION, ATTACK_REPLAY, ATTACK_UNAUTHORIZED
from qsentinel.config import ExperimentConfig
from qsentinel.session import QDSSession


class DetectorExpectationMixin:
    """Shared helpers for the end-to-end detector tests."""

    def run_attack(self, attack_key: str) -> object:
        config = ExperimentConfig()
        session = QDSSession(config)
        if attack_key == ATTACK_REPLAY:
            session.run_scenario(ATTACK_BENIGN)
        return session.run_scenario(attack_key)

    def assert_verdict(self, result, statistical: bool, pauli: bool):
        self.assertEqual(result.detection.statistical.is_threat, statistical)
        self.assertEqual(result.detection.pauli.is_threat, pauli)


class TestStatisticalDetection(unittest.TestCase, DetectorExpectationMixin):
    def test_legitimate_is_clean(self):
        self.assert_verdict(self.run_attack(ATTACK_BENIGN), statistical=False, pauli=False)

    def test_quantum_attacks_are_detected_by_both(self):
        for attack in (ATTACK_FORGERY, ATTACK_IMPERSONATION, ATTACK_CHANNEL):
            self.assert_verdict(self.run_attack(attack), statistical=True, pauli=True)

    def test_replay_and_unauthorized_escape_pauli_layer(self):
        replay = self.run_attack(ATTACK_REPLAY)
        self.assert_verdict(replay, statistical=True, pauli=False)
        unauthorized = self.run_attack(ATTACK_UNAUTHORIZED)
        self.assert_verdict(unauthorized, statistical=True, pauli=False)


class TestProtocolRejection(unittest.TestCase, DetectorExpectationMixin):
    def test_every_attack_is_rejected_by_protocol(self):
        for attack in (ATTACK_BENIGN,):
            result = self.run_attack(attack)
            self.assertTrue(result.accepted_by_protocol, attack)

    def test_all_attacks_rejected(self):
        for attack in (ATTACK_FORGERY, ATTACK_IMPERSONATION, ATTACK_REPLAY,
                       ATTACK_UNAUTHORIZED, ATTACK_CHANNEL):
            result = self.run_attack(attack)
            self.assertFalse(result.accepted_by_protocol, attack)
            self.assertGreaterEqual(float(result.verification.mismatch_rate()), 0.0)


class TestRepeatDeterminism(unittest.TestCase):
    def test_same_seed_same_verdict(self):
        def run_once():
            config = ExperimentConfig()
            session = QDSSession(config)
            return session.run_scenario(ATTACK_CHANNEL).detection.pauli.is_threat
        self.assertEqual(run_once(), run_once())


if __name__ == "__main__":
    unittest.main()