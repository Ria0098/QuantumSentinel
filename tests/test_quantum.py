"""Tests for the exact quantum mechanics core."""

from __future__ import annotations

import unittest

import numpy as np

from qsentinel.quantum.gates import I, PAULI, X, Z, to_computational, to_eigenbasis
from qsentinel.quantum.measurement import measure_pauli, pauli_expectation
from qsentinel.quantum.statevector import StateVector
from qsentinel.quantum.states import bell_pair, pauli_eigenstate


class TestStateVector(unittest.TestCase):
    def test_basis_state_is_normalised(self):
        state = StateVector.from_label("01")
        self.assertEqual(state.num_qubits, 2)
        self.assertAlmostEqual(float(np.sum(state.probabilities())), 1.0)

    def test_computational_measurement_collapses(self):
        rng = np.random.default_rng(7)
        bell = StateVector.from_superposition(["00", "11"], [1.0, 1.0])
        bits, collapsed = bell.measure_qubits((0, 1), rng)
        self.assertTrue(bits == (0, 0) or bits == (1, 1))
        self.assertAlmostEqual(collapsed.fidelity(StateVector.from_label("".join(map(str, bits)))), 1.0)

    def test_one_qubit_rotation_store_round_trip(self):
        for basis in ("X", "Y", "Z"):
            matrix = to_computational(basis) @ to_eigenbasis(basis)
            self.assertTrue(np.allclose(matrix, I, atol=1e-12), basis)

    def test_pauli_anticommute_relations(self):
        self.assertTrue(np.allclose(X @ Z, -Z @ X, atol=1e-12))


class TestPauliEigenstates(unittest.TestCase):
    def test_eigenvalue_correct(self):
        for basis in ("X", "Y", "Z"):
            for bit in (0, 1):
                state = pauli_eigenstate(bit, basis)
                expected = 1 - 2 * bit
                measured = np.real(state.expectation(PAULI[basis]))
                self.assertAlmostEqual(measured, float(expected), places=10)

    def test_measurement_deterministic_for_eigenstate(self):
        rng = np.random.default_rng(3)
        for basis in ("X", "Y", "Z"):
            for bit in (0, 1):
                outcome = measure_pauli(pauli_eigenstate(bit, basis), 0, basis, rng)
                self.assertEqual(outcome.eigenvalue, 1 - 2 * bit)


class TestBellPairs(unittest.TestCase):
    def test_eigenvalue_and_basis(self):
        for basis in ("Z", "X"):
            for eigenvalue in (-1, 1):
                state = bell_pair(eigenvalue, basis)
                # Along the resource's own axis the correlator is always +1; the
                # other axis carries the Bell eigenvalue.
                e_own = np.real(state.expectation(np.kron(PAULI[basis], PAULI[basis])))
                other = "X" if basis == "Z" else "Z"
                e_other = np.real(state.expectation(np.kron(PAULI[other], PAULI[other])))
                self.assertAlmostEqual(e_own, 1.0, places=10, msg=(basis, eigenvalue))
                self.assertAlmostEqual(e_other, float(eigenvalue), places=10, msg=(basis, eigenvalue))

    def test_bell_marginal_is_maximally_mixed(self):
        # The single-qubit marginal of a Bell pair is the maximally mixed state.
        # Compute the partial trace directly rather than relying on the
        # dominant-eigenvector approximation the protocol uses.
        state = bell_pair(1, "Z")
        tensor = state.amplitudes.reshape((2, 2))
        rho = tensor @ tensor.conj().T
        values = np.real(np.linalg.eigvalsh(rho))
        self.assertTrue(np.allclose(np.sort(values), [0.5, 0.5], atol=1e-6))

    def test_correlator_pattern_matches_ideal(self):
        from qsentinel.quantum.measurement import correlator
        for basis, other in (("Z", "X"), ("X", "Z")):
            state = bell_pair(1, basis)
            self.assertAlmostEqual(correlator(state, basis, basis), 1.0, places=9)
            self.assertAlmostEqual(correlator(state, other, other), 1.0, places=9)
            self.assertAlmostEqual(correlator(state, "Z", "X"), 0.0, places=9)
            self.assertAlmostEqual(correlator(state, "X", "Z"), 0.0, places=9)


class TestExpectations(unittest.TestCase):
    def test_plus_plus_plus_plus_decomposition(self):
        # (|0>+|1>)/sqrt2 should have only X expectation +1
        plus = StateVector.from_superposition(["0", "1"], [1.0 / np.sqrt(2.0)] * 2)
        self.assertAlmostEqual(pauli_expectation(plus, 0, "X"), 1.0, places=9)


if __name__ == "__main__":
    unittest.main()