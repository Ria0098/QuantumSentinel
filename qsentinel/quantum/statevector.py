"""Exact state-vector simulation primitives for small qubit registers.

The prototype only ever needs registers of one to three qubits for exact
state evolution (test qubits, Bell pairs, the three-qubit teleportation
circuit), so a dense state vector is both exact and cheap.  Multi-qubit
parity checks are evaluated exactly by :mod:`qsentinel.quantum.measurement`,
which exploits the product structure of the distributed state.
"""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np

Tensor = np.ndarray


class StateVector:
    """A pure state of ``num_qubits`` qubits stored as a dense amplitude array.

    Qubit ``0`` is the most significant bit of the computational basis label,
    so a two-qubit label ``"01"`` denotes the basis state ``|01>`` with qubit
    ``0`` in ``|0>`` and qubit ``1`` in ``|1>``.
    """

    __slots__ = ("num_qubits", "_amplitudes")

    def __init__(self, amplitudes: Iterable[complex], num_qubits: int) -> None:
        data = np.asarray(list(amplitudes), dtype=complex)
        expected = 1 << num_qubits
        if data.shape != (expected,):
            raise ValueError(
                f"expected {expected} amplitudes for {num_qubits} qubits, got {data.shape}"
            )
        norm = float(np.linalg.norm(data))
        if norm <= 0.0:
            raise ValueError("state vector must be non-zero")
        object.__setattr__(self, "num_qubits", num_qubits)
        object.__setattr__(self, "_amplitudes", data / norm)

    @classmethod
    def zero(cls, num_qubits: int) -> "StateVector":
        """Return ``|0...0>``."""
        return cls.from_label("0" * num_qubits)

    @classmethod
    def from_label(cls, label: str) -> "StateVector":
        """Return the computational basis state ``label``."""
        clean = "".join(ch for ch in label if ch in "01")
        if not clean:
            raise ValueError("basis label must contain at least one bit")
        index = int(clean, 2)
        amplitudes = np.zeros(1 << len(clean), dtype=complex)
        amplitudes[index] = 1.0
        return cls(amplitudes, len(clean))

    @classmethod
    def from_superposition(cls, labels: Sequence[str], coeffs: Sequence[complex]) -> "StateVector":
        """Return ``sum(coeffs[k] * |labels[k]>)`` normalised."""
        if len(labels) != len(coeffs):
            raise ValueError("labels and coeffs must have equal length")
        num_qubits = len(labels[0])
        amplitudes = np.zeros(1 << num_qubits, dtype=complex)
        for label, coeff in zip(labels, coeffs):
            amplitudes[int(label, 2)] += coeff
        return cls(amplitudes, num_qubits)

    @property
    def amplitudes(self) -> np.ndarray:
        """Read-only view of the amplitude array."""
        view = self._amplitudes.view()
        view.flags.writeable = False
        return view

    def probabilities(self) -> np.ndarray:
        """Born-rule probabilities for every computational basis outcome."""
        return np.abs(self._amplitudes) ** 2

    def sample(self, rng: np.random.Generator, num_samples: int = 1) -> np.ndarray:
        """Draw ``num_samples`` computational-basis outcomes as integer labels."""
        probs = self.probabilities()
        probs = probs / probs.sum()
        return rng.choice(probs.size, size=num_samples, p=probs)

    def expectation(self, observable: np.ndarray) -> complex:
        """Exact expectation value of a 2^n x 2^n Hermitian observable."""
        return complex(np.vdot(self._amplitudes, observable @ self._amplitudes))

    def apply_one_qubit(self, gate: np.ndarray, qubit: int) -> "StateVector":
        """Return a new state with ``gate`` applied to ``qubit``."""
        if qubit < 0 or qubit >= self.num_qubits:
            raise IndexError(f"qubit {qubit} out of range for {self.num_qubits} qubits")
        gate = np.asarray(gate, dtype=complex)
        if gate.shape != (2, 2):
            raise ValueError("gate must be 2x2")
        n = self.num_qubits
        tensor = self._amplitudes.reshape((2,) * n)
        tensor = np.tensordot(gate, tensor, axes=([1], [qubit]))
        tensor = np.moveaxis(tensor, 0, qubit)
        return StateVector(tensor.reshape(-1), n)

    def apply_controlled_not(self, control: int, target: int) -> "StateVector":
        """Return a new state with a CNOT from ``control`` to ``target``."""
        if control == target:
            raise ValueError("control and target must differ")
        if not 0 <= control < self.num_qubits or not 0 <= target < self.num_qubits:
            raise IndexError("qubit index out of range")
        n = self.num_qubits
        tensor = self._amplitudes.reshape((2,) * n)
        kernel = CNOT.reshape((2, 2, 2, 2))
        tensor = np.tensordot(kernel, tensor, axes=([2, 3], [control, target]))
        return StateVector(tensor.reshape(-1), n)

    def append_qubit(self, value: int) -> "StateVector":
        """Return a new state with one extra qubit set to ``value`` (0 or 1)."""
        if value not in (0, 1):
            raise ValueError("qubit value must be 0 or 1")
        tensor = np.tensordot(
            np.eye(2, dtype=complex)[:, value], self._amplitudes, axes=0
        )
        return StateVector(tensor, self.num_qubits + 1)

    def project(self, label: str) -> "StateVector":
        """Return the normalised state obtained by projecting onto ``|label>``."""
        index = int(label, 2)
        if self.probabilities()[index] <= 1e-15:
            raise ValueError(f"cannot project {self.num_qubits}-qubit state onto |{label}>")
        projected = np.zeros_like(self._amplitudes)
        projected[index] = self._amplitudes[index]
        return StateVector(projected, self.num_qubits)

    def measure_qubits(
        self, qubits: Sequence[int], rng: np.random.Generator
    ) -> tuple[tuple[int, ...], "StateVector"]:
        """Measure ``qubits`` in the computational basis and collapse the register.

        Returns the outcome bits in the order the qubits were given, together
        with the post-measurement state.  Qubits that are *not* measured are
        left unobserved: the collapse projects onto the subspace spanned by
        the measured outcomes, which is what keeps an entangled partner pure.
        """
        n = self.num_qubits
        targets = list(dict.fromkeys(qubits))
        for qubit in targets:
            if not 0 <= qubit < n:
                raise IndexError("qubit index out of range")
        if not targets:
            return (), self.copy()
        keep = [qubit for qubit in range(n) if qubit not in targets]
        order = targets + keep
        tensor = self._amplitudes.reshape((2,) * n)
        permuted = np.transpose(tensor, order)
        flat = permuted.reshape(1 << len(targets), -1)
        probs = (np.abs(flat) ** 2).sum(axis=1)
        total = probs.sum()
        if total <= 0.0:
            raise ValueError("state has no support on the measured subspace")
        index = int(rng.choice(flat.shape[0], p=probs / total))
        label = format(index, f"0{len(targets)}b")
        collapsed = np.zeros_like(flat)
        collapsed[index] = flat[index]
        reshaped = collapsed.reshape((2,) * n)
        restored = np.transpose(reshaped, np.argsort(order))
        bits = tuple(int(bit) for bit in label)
        return bits, StateVector(restored.reshape(-1), n)

    def copy(self) -> "StateVector":
        """Return an independent copy of this state."""
        return StateVector(self._amplitudes.copy(), self.num_qubits)

    def sample_label(self, rng: np.random.Generator) -> str:
        """Sample one computational-basis outcome and return its label."""
        index = int(self.sample(rng, 1)[0])
        return format(index, f"0{self.num_qubits}b")

    def label(self) -> str:
        """Computational basis label of the (necessarily classical) state."""
        nonzero = np.flatnonzero(np.abs(self._amplitudes) > 1e-12)
        if nonzero.size != 1:
            raise ValueError("state is not a computational basis state")
        return format(int(nonzero[0]), f"0{self.num_qubits}b")

    def reduced_single_qubit(self, qubit: int) -> "StateVector":
        """Return the dominant eigenvector of the one-qubit marginal on ``qubit``.

        For the product states used by the protocol every marginal is pure, so
        the dominant eigenvector reproduces the exact single-qubit state and
        keeps all Pauli expectation values exact.
        """
        n = self.num_qubits
        tensor = self._amplitudes.reshape((2,) * n)
        moved = np.moveaxis(tensor, qubit, 0).reshape(2, -1)
        rho = moved @ moved.conj().T
        values, vectors = np.linalg.eigh(rho)
        best = int(np.argmax(values.real))
        return StateVector(vectors[:, best], 1)

    def fidelity(self, other: "StateVector") -> float:
        """Squared-overlap (fidelity) between two pure states."""
        if other.num_qubits != self.num_qubits:
            raise ValueError("states must act on the same number of qubits")
        overlap = np.vdot(self._amplitudes, other._amplitudes)
        return float(min(1.0, abs(overlap) ** 2))

    def entropy(self) -> float:
        """Von Neumann entropy of the single-qubit marginal (bits)."""
        rho = self.reduced_single_qubit(0).density_matrix()
        vals = np.clip(np.real(np.linalg.eigvalsh(rho)), 0.0, 1.0)
        vals = vals[vals > 1e-12]
        return float(-np.sum(vals * np.log2(vals)))

    def density_matrix(self) -> np.ndarray:
        """Density matrix of a one-qubit state."""
        vec = self._amplitudes
        return np.outer(vec, vec.conj())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StateVector):
            return NotImplemented
        return (
            self.num_qubits == other.num_qubits
            and bool(np.allclose(self._amplitudes, other._amplitudes))
        )

    def __repr__(self) -> str:
        rounded = np.round(self._amplitudes, 4)
        terms = [
            f"{amp}|{format(i, f'0{self.num_qubits}b')}>"
            for i, amp in enumerate(rounded)
            if abs(amp) > 1e-9
        ]
        return f"StateVector({self.num_qubits}q: {' + '.join(terms)})"


CNOT = np.array(
    [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=complex
)
