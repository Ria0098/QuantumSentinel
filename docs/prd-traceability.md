# PRD traceability (S. No. 26141)

Mapping between the problem statement's functional requirements and the
implementation.  The identifiers (FR-*) are the sections of the SIH 2026
problem brief for "Quantum-Inspired Cyber Threat Detection for Digital
Signature Security".

| Requirement | Implementation | Status |
| ----------- | -------------- | ------ |
| FR-01 Understand and simulate the Quantum Digital Signature flow | `qsentinel/protocol/`, `qsentinel/protocol/teleportation.py`, `docs/math.md` | Implemented |
| FR-02 Understand and simulate quantum teleportation | `qsentinel/protocol/teleportation.py` (exact 3-qubit circuit, Pauli correction), `tests/test_teleportation.py` | Implemented |
| FR-03 Build a quantum/classical simulation of the QDS signature and verification flow | `qsentinel/session.py`, `qsentinel/channel.py`, `scripts/generate_report.py` | Implemented |
| FR-04 Simulate and implement quantum attacks | `qsentinel/attacks/` (forgery, impersonation, replay, unauthorized, channel), `docs/attacks.md` | Implemented |
| FR-05 Detect quantum attacks using a quantum-inspired detection model | Two non-AI layers: `qsentinel/detection/statistical.py` and `pauli.py`; `DetectionEngine` combines them | Implemented |
| FR-06 Model and simulate a quantum attack dataset | `qsentinel/attacks/` + `QuantumChannel` noise model; labelled trials in `qsentinel/evaluation/runner.py` | Implemented |
| FR-07 Evaluate the model; report detection rate and accuracy | `qsentinel/evaluation/{metrics,runner}.py`, `docs/results.md`, `results/evaluation.json` | Implemented |
| FR-08 (Submission) architecture, math and results documentation | `docs/architecture.md`, `docs/math.md`, `docs/results.md` | Implemented |
| FR-09 (Submission) runnable demo | `run_demo.py`, `qsentinel/cli.py`, `scripts/` | Implemented |
| FR-10 (Submission) working prototype via UI/CLI | `qsentinel/cli.py` (`scenarios`, `demo`, `evaluate`, `noise-sweep`, `group-sweep`); console tables + JSON/Markdown export | Implemented |
| FR-11 No AI/ML is required for detection | Both layers are fixed arithmetic/classical rules; nothing is trained or fitted | Implemented |
| FR-12 Produce quantitative results: detection rate, false-alarm rate, accuracy | `ConfusionMatrix` + Wilson 95% intervals in `qsentinel/evaluation/metrics.py` | Implemented |
| FR-13 Quantum measurement statistics are computed from the circuit, not faked | Every statistic flows through `measure_pauli` / `parity_measurement` / `correlator` over exact state vectors | Implemented |
| FR-14 Pre-defined thresholds on measurement data | `DetectionConfig` (single source, documented defaults) | Implemented |
| FR-15 Measure outcomes cover the full range of measurement statistics | eigenvalue agreement, basis distributions, cat-state parity, two-body correlators | Implemented |
| FR-16 Compare detection methods / baselines | `DetectionEngine` runs both layers on the shared `DetectionInput`; `docs/detection.md` | Implemented |
| FR-17 Run evaluation over noise and amplification settings | `run_noise_sweep`, `run_group_size_sweep`, `results/noise_sweep.json`, `results/group_sweep.json` | Implemented |
| FR-18 Deliverables: code, docs, results, demo, README | Complete repository under `~/Desktop/QuantumSentinel` | Implemented |

## Threat-model coverage table

| PRD threat | Attack module | Detected by | Notes |
| ---------- | ------------- | ----------- | ----- |
| Signature forgery | `SignatureForgery` | statistical + Pauli | guessed-key mismatch in measurement data |
| Sender impersonation | `Impersonation` | statistical + Pauli | well-formed signature bound to wrong key |
| Replay | `ReplayAttack` | statistical only | quantum-invisible; nonce cache |
| Unauthorised verification | `UnauthorizedVerification` | statistical only | quantum-invisible; authorisation rule |
| Quantum channel manipulation | `ChannelManipulation` | statistical + Pauli | Pauli/tamper/loss + witness disturbance |