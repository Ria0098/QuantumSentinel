"""Attack simulation: the five SIH threat classes plus a benign baseline.

Adding a new attack means subclassing :class:`Attack`, implementing
:meth:`Attack.run`, and registering the instance - no change to the QDS
protocol, the channel, the detectors or the CLI is required.
"""

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
    AttackContext,
    AttackOutcome,
    BenignExchange,
)
from .channel_manipulation import ChannelManipulation
from .forgery import SignatureForgery
from .impersonation import Impersonation
from .registry import (
    ATTACKS,
    build_registry,
    default_registry,
    describe_attacks,
)
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
    "AttackContext",
    "AttackOutcome",
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
