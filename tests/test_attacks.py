"""Tests for the five attack simulations and the registry."""

from __future__ import annotations

import unittest

from qsentinel.attacks import (
    ATTACK_BENIGN,
    ATTACK_CHANNEL,
    ATTACK_FORGERY,
    ATTACK_IMPERSONATION,
    ATTACK_ORDER,
    ATTACK_REPLAY,
    ATTACK_TITLES,
    ATTACK_UNAUTHORIZED,
    AttackContext,
    AttackOutcome,
    BenignExchange,
    ChannelManipulation,
    Impersonation,
    ReplayAttack,
    SignatureForgery,
    UnauthorizedVerification,
    default_registry,
    describe_attacks,
)
from qsentinel.config import ExperimentConfig
from qsentinel.protocol.freshness import ReplayCache
from qsentinel.protocol.sender import make_transaction


def _context(seed: int = 1) -> AttackContext:
    config = ExperimentConfig()
    rng = config.rng(seed)
    txn = make_transaction(rng, 8)
    return AttackContext(
        transaction=txn,
        config=config,
        rng=rng,
        replay_cache=ReplayCache(),
        authorised_entities=frozenset({"alice", "victor"}),
    )


class TestRegistry(unittest.TestCase):
    def test_all_five_attacks_are_present(self):
        registry = default_registry()
        for key in (ATTACK_FORGERY, ATTACK_IMPERSONATION, ATTACK_REPLAY,
                    ATTACK_UNAUTHORIZED, ATTACK_CHANNEL):
            self.assertIn(key, registry)

    def test_attack_order_matches_problem_statement_grouping(self):
        self.assertEqual(ATTACK_ORDER[0], ATTACK_BENIGN)
        self.assertEqual(set(ATTACK_ORDER[1:]), {ATTACK_FORGERY, ATTACK_IMPERSONATION,
                                                 ATTACK_REPLAY, ATTACK_UNAUTHORIZED,
                                                 ATTACK_CHANNEL})

    def test_titles_cover_every_attack(self):
        for key in ATTACK_ORDER:
            self.assertEqual(ATTACK_TITLES[key], ATTACK_TITLES[key])

    def test_describe_attacks_is_json_friendly(self):
        payload = describe_attacks()
        self.assertIn(ATTACK_FORGERY, payload)


class TestBenign(unittest.TestCase):
    def test_leaves_transaction_untouched(self):
        context = _context()
        outcome = BenignExchange().run(context)
        self.assertIsInstance(outcome, AttackOutcome)
        self.assertEqual(outcome.transaction, context.transaction)
        self.assertEqual(outcome.disturbances, ())


class TestForgery(unittest.TestCase):
    def test_produces_signature_override(self):
        context = _context()
        outcome = SignatureForgery().run(context)
        self.assertTrue(outcome.rewrites_signature)

    def test_has_quantum_footprint(self):
        self.assertTrue(SignatureForgery.expected_quantum_visible)


class TestImpersonation(unittest.TestCase):
    def test_swaps_the_key_to_the_attackers(self):
        context = _context()
        original_key = context.transaction.key
        outcome = Impersonation().run(context)
        self.assertNotEqual(outcome.transaction.key, original_key)
        self.assertTrue(outcome.rewrites_signature)

    def test_still_claims_to_be_the_real_sender(self):
        context = _context()
        outcome = Impersonation().run(context)
        self.assertEqual(outcome.transaction.requesting_entity, context.transaction.requesting_entity)
        self.assertTrue(outcome.transaction.authorised)
        self.assertTrue(outcome.expected_quantum_visible)


class TestReplay(unittest.TestCase):
    def test_requires_history(self):
        context = _context()
        with self.assertRaises(RuntimeError):
            ReplayAttack().run(context)

    def test_replays_last_accepted_transaction(self):
        config = ExperimentConfig()
        rng = config.rng(2)
        original = make_transaction(rng, 8)
        context = AttackContext(
            transaction=original,
            config=config,
            rng=rng,
            replay_cache=ReplayCache(),
            authorised_entities=frozenset({"alice", "victor"}),
            accepted_history=(original,),
        )
        outcome = ReplayAttack().run(context)
        self.assertEqual(outcome.transaction.message, original.message)
        self.assertEqual(outcome.transaction.nonce, original.nonce)
        self.assertEqual(outcome.expected_quantum_visible, False)


class TestUnauthorized(unittest.TestCase):
    def test_sets_root_cause(self):
        context = _context()
        outcome = UnauthorizedVerification().run(context)
        self.assertFalse(outcome.transaction.authorised)
        self.assertEqual(outcome.expected_quantum_visible, False)


class TestChannelManipulation(unittest.TestCase):
    def test_injects_channel_disturbances(self):
        from qsentinel.channel import DISTURBANCE_KINDS
        context = _context()
        outcome = ChannelManipulation().run(context)
        self.assertTrue(outcome.disturbances)
        for disturbance in outcome.disturbances:
            self.assertIn(disturbance.kind, DISTURBANCE_KINDS)


if __name__ == "__main__":
    unittest.main()