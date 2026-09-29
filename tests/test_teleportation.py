"""Tests for the exact three-qubit teleportation circuit."""

from __future__ import annotations

import unittest

import numpy as np

from qsentinel.quantum.states import bell_pair, pauli_eigenstate
from qsentinel.protocol.teleportation import (
    correction_pauli,
    residual_pauli,
    teleport,
)


def _all_single_qubit_eigenstates() -> list:
    states = []
    for basis in ("X", "Y", "Z"):
        for bit in (0, 1):
            states.append(pauli_eigenstate(bit, basis))
    return states


class TestFaithfulTeleportation(unittest.TestCase):
    def test_fidelity_1_for_all_bases_and_bell_lambdas(self):
        rng = np.random.default_rng(11)
        for payload in _all_single_qubit_eigenstates():
            for basis in ("Z", "X"):
                bell = bell_pair(1, basis)
                received, record = teleport(payload, bell, rng)
                self.assertEqual(record.residual_error, "I")
                self.assertAlmostEqual(received.fidelity(payload), 1.0, places=9)

    def test_teleportation_consumes_two_classical_bits(self):
        payload = pauli_eigenstate(0, "Z")
        rng = np.random.default_rng(2)
        _, record = teleport(payload, bell_pair(1, "Z"), rng)
        self.assertEqual(len(record.true_message), 2)


class TestTamperedControlChannel(unittest.TestCase):
    def test_wrong_correction_leaves_residual_pauli(self):
        rng = np.random.default_rng(5)
        payload = pauli_eigenstate(0, "Z")
        received, record = teleport(payload, bell_pair(1, "Z"), rng, tamper=True)
        self.assertEqual(record.message_was_tampered, True)
        self.assertNotEqual(record.residual_error, "I")

    def test_delivered_message_override(self):
        rng = np.random.default_rng(5)
        payload = pauli_eigenstate(0, "Z")
        received, record = teleport(
            payload, bell_pair(1, "Z"), rng, used_message=(1, 0)
        )
        self.assertEqual(record.used_message, (1, 0))
        self.assertEqual(record.applied_correction, correction_pauli(1, 0))


class TestResidualFormula(unittest.TestCase):
    def test_residual_table(self):
        # residual = correction_pauli(true_m1 ^ used_m1, true_m2 ^ used_m2)
        cases = {
            ((0, 0), (0, 0)): "I",
            ((0, 1), (1, 1)): "Z",
            ((1, 0), (1, 1)): "X",
            ((1, 1), (0, 1)): "Z",
            ((0, 0), (1, 1)): "Y",
            ((0, 1), (0, 0)): "X",
            ((1, 0), (0, 0)): "Z",
        }
        for (truth, used), expected in cases.items():
            self.assertEqual(residual_pauli(*truth, *used), expected)

    def test_random_pauli_anticommute_behaviour(self):
        # A random non-identity Pauli flips a Z eigenstate ~2/3 of the time
        rng = np.random.default_rng(1)
        flips = 0
        trials = 3000
        for _ in range(trials):
            payload = pauli_eigenstate(0, "Z")
            received, _ = teleport(payload, bell_pair(1, "Z"), rng, tamper=True)
            eigenvalue = np.real(received.expectation(np.array([[1, 0], [0, -1]])))
            if eigenvalue < 0:
                flips += 1
        self.assertGreater(flips / trials, 0.55)
        self.assertLess(flips / trials, 0.80)


if __name__ == "__main__":
    unittest.main()