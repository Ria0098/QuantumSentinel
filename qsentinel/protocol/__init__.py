"""QDS protocol: sender signing, teleportation distribution, and verification."""

from .freshness import ReplayCache
from .sender import generate_key, generate_message, make_transaction, sign
from .state import (
    CheckResult,
    DistributedState,
    QDSTransaction,
    SignatureBlock,
    TestQubit,
    VerificationReport,
    WitnessPair,
)
from .teleportation import TeleportationRecord, correction_pauli, residual_pauli, teleport
from .verifier import (
    amplification_checks,
    coverage_checks,
    expectation_statistics,
    parity_groups,
    single_qubit_checks,
    verify,
    witness_checks,
)

__all__ = [
    "CheckResult",
    "DistributedState",
    "QDSTransaction",
    "ReplayCache",
    "SignatureBlock",
    "TeleportationRecord",
    "TestQubit",
    "VerificationReport",
    "WitnessPair",
    "amplification_checks",
    "coverage_checks",
    "correction_pauli",
    "expectation_statistics",
    "generate_key",
    "generate_message",
    "make_transaction",
    "parity_groups",
    "residual_pauli",
    "sign",
    "single_qubit_checks",
    "teleport",
    "verify",
    "witness_checks",
]
