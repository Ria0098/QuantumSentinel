# Architecture

QuantumSigGuard is a pure-NumPy prototype of a **quantum-inspired cyber threat
detection system for teleportation-based Quantum Digital Signatures (QDS)**. It
simulates a qubit-wise QDS protocol, five adversarial scenarios, and **two
non-AI/ML detection layers**, and evaluates them with controlled experiments.

```
             ┌───────────────┐     classical (key, message, nonce)
   Sender    │  QDSSession   │──────────────────────────────┐
   (alice)   └───────┬───────┘                              │
                     │ sign()                 ┌──────────────▼──────────────┐
                     ▼ signature qubits      │  QuantumChannel.transmit()   │
              SignatureBlock ───────────────►│  · teleport each signature    │
                                             │    qubit through a Bell pair  │
                                             │  · physical noise model       │
                                             │  · attack disturbances        │
                                             └──────────────┬──────────────┘
                                                            ▼
                                           DistributedState (what arrived)
                                                            │
                              ┌─────────────────────────────┼──────────────────┐
                              ▼                             ▼                  ▼
                       Verifier.verify()          StatisticalDetector   PauliMeasurementDetector
                       single/parity/witness       (Method 1)            (Method 2)
                       coverage/freshness/auth      threshold rules       measurement-only rules
                              │                             │                  │
                              ▼                             └────────┬─────────┘
                       VerificationReport                  DetectionEngine
                                                                    │
                                                                    ▼
                                                             ScenarioResult
```

## Package layout

| Path | Responsibility |
| ---- | -------------- |
| `qsentinel/quantum/` | Exact state-vector engine, Pauli gates and bases, measurements, Bell states, teleportation |
| `qsentinel/protocol/` | Sender, distribution/channel, receiver/verifier, freshness cache, data structures |
| `qsentinel/attacks/` | Five attack simulations plus the benign baseline |
| `qsentinel/detection/` | Statistical layer, Pauli-measurement layer, and the combining engine |
| `qsentinel/evaluation/` | Confusion-matrix metrics, controlled experiments, parameter sweeps |
| `qsentinel/reporting/` | Console rendering and JSON/Markdown export |
| `qsentinel/session.py` | Stateful end-to-end driver (`run_scenario`) |
| `qsentinel/config.py` | Single source of truth for every tunable value |
| `qsentinel/cli.py` | `qsentinel` command: scenarios, demo, evaluate, noise-sweep, group-sweep |
| `scripts/` | Benchmark, evaluation and full report-generation entry points |
| `tests/` | `unittest` suite (`python -m unittest discover -s tests`) |

## Layering rules

1. **The quantum core never knows about signatures or attacks.** It only exposes
   states, gates and measurement statistics.
2. **Attack *generation* is separate from protocol *execution*.** An attack
   produces a declarative `AttackOutcome` (possibly-swapped transaction, forged
   signature block, channel disturbances). The channel executes disturbances; it
   never imports the attacks package.
3. **Both detectors consume the same `DetectionInput`.** The statistical layer
   reads verification *counts* and classical protocol context (freshness,
   authorisation). The Pauli layer reads only *measurement data and the verifier's
   record of the message*. This shared-input design is what makes the two-layer
   comparison fair.
4. **The verifier judges against its own record, never against the attacker's.**
   `QuantumChannel.transmit` takes an explicit trusted `reference` transaction and
   derives the expected bases/eigenvalues from it, so a self-consistent forged
   transaction cannot verify against its own expectations.

## No AI / no ML

Neither detector learns anything. Every signal is a closed-form statistic of the
measurement data or a classical protocol rule, compared against a fixed constant
threshold from `DetectionConfig`. There are no fitted parameters, no training
phase and no learned model anywhere in `qsentinel/`.

## The session the user interacts with

`QDSSession` owns the two pieces of *long-lived verifier state* that a single
transaction does not: the **replay cache** (nonces already accepted) and the
**accepted history** (used by replay-attack simulation). Calling
`session.run_scenario("replay")` therefore requires the session to have accepted
at least one prior transaction; the evaluation runner seeds that history
automatically.