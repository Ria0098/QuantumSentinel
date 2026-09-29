"""Replay protection: the classical freshness layer.

Quantum measurement statistics are, by construction, blind to *repetition* of
previously valid data.  A replayed transaction is bit-for-bit identical to the
original, so every Pauli observable returns exactly the same expectation
values.  Detecting replay therefore requires a classical freshness mechanism,
and the prototype is explicit about that rather than pretending the quantum
layer can do it.
"""

from __future__ import annotations

from collections import OrderedDict

from .state import QDSTransaction


class ReplayCache:
    """Bounded set of nonces already accepted by the verifier."""

    def __init__(self, capacity: int = 512) -> None:
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._seen: OrderedDict[str, str] = OrderedDict()

    def __len__(self) -> int:
        return len(self._seen)

    def __contains__(self, nonce: str) -> bool:
        return nonce in self._seen

    def remember(self, transaction: QDSTransaction) -> None:
        """Record an accepted transaction's nonce, evicting the oldest if full."""
        if transaction.nonce in self._seen:
            self._seen.move_to_end(transaction.nonce)
            return
        self._seen[transaction.nonce] = transaction.transaction_id
        while len(self._seen) > self.capacity:
            self._seen.popitem(last=False)

    def is_fresh(self, transaction: QDSTransaction) -> bool:
        """True when the nonce has not been accepted before."""
        return transaction.nonce not in self._seen

    def clear(self) -> None:
        """Forget every nonce."""
        self._seen.clear()
