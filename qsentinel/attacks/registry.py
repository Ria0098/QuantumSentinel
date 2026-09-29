"""Registry of the five SIH attack classes plus the benign baseline."""

from __future__ import annotations

from typing import Iterable

from .base import (
    ATTACK_BENIGN,
    ATTACK_CHANNEL,
    ATTACK_FORGERY,
    ATTACK_IMPERSONATION,
    ATTACK_ORDER,
    ATTACK_REPLAY,
    ATTACK_TITLES,
    ATTACK_UNAUTHORIZED,
    Attack,
    BenignExchange,
)
from .channel_manipulation import ChannelManipulation
from .forgery import SignatureForgery
from .impersonation import Impersonation
from .replay import ReplayAttack
from .unauthorized import UnauthorizedVerification

__all__ = [
    "ATTACKS",
    "ATTACK_BENIGN",
    "ATTACK_CHANNEL",
    "ATTACK_FORGERY",
    "ATTACK_IMPERSONATION",
    "ATTACK_ORDER",
    "ATTACK_REPLAY",
    "ATTACK_TITLES",
    "ATTACK_UNAUTHORIZED",
    "Attack",
    "BenignExchange",
    "ChannelManipulation",
    "Impersonation",
    "ReplayAttack",
    "SignatureForgery",
    "UnauthorizedVerification",
    "build_registry",
    "default_registry",
    "describe_attacks",
]

#: The five threat classes named in the SIH problem statement.
ATTACKS: tuple[str, ...] = (
    ATTACK_FORGERY,
    ATTACK_IMPERSONATION,
    ATTACK_REPLAY,
    ATTACK_UNAUTHORIZED,
    ATTACK_CHANNEL,
)


def default_registry() -> dict[str, Attack]:
    """Return a fresh mapping of attack key to a default-constructed attack."""
    return {
        ATTACK_BENIGN: BenignExchange(),
        ATTACK_FORGERY: SignatureForgery(),
        ATTACK_IMPERSONATION: Impersonation(),
        ATTACK_REPLAY: ReplayAttack(),
        ATTACK_UNAUTHORIZED: UnauthorizedVerification(),
        ATTACK_CHANNEL: ChannelManipulation(),
    }


def build_registry(instances: Iterable[Attack]) -> dict[str, Attack]:
    """Return a registry of caller-supplied attack instances."""
    return {attack.key: attack for attack in instances}


def describe_attacks() -> dict[str, dict[str, object]]:
    """Return a JSON-friendly description of every registered attack."""
    registry = default_registry()
    return {
        key: {
            "title": attack.title,
            "description": attack.description,
            "expected_quantum_visible": attack.expected_quantum_visible,
        }
        for key, attack in registry.items()
    }
