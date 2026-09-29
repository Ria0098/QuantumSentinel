# Security & Access Document

**Smart India Hackathon 2026 — Problem Statement SIH26141** · **Egreen Quanta LLP** · **Category: Software · Theme: Security**
**Project:** *Quantum-Inspired Cyber Threat Detection for Digital Signature Security*
**Document Type:** Security & Access · Status: Prototype Documentation / SIH Submission · Version: 1.0

> This document describes the security and access posture of the **implemented** prototype
> **QuantumSigGuard** (`~/Desktop/QuantumSentinel`). Every status below is corroborated by source
> code and measured output referenced in the **Evidence map (§13.2)**. Two facts shape the whole
> document:
>
> 1. The prototype is a **local, single-user, terminal-based simulator** (Python + NumPy). It has
>    **no web/API server, no database, no accounts, no network exposure and no real quantum
>    hardware**. App-security controls that only exist in web deployments (auth, RBAC, TLS, CORS,
>    CSRF, rate limiting, containers) are therefore marked **N/A (no such component)** rather than
>    "Planned", and the conditions under which they would become relevant are stated.
> 2. Security *within the simulated protocol* — replay protection, authorisation, freshness,
>    input validation, deterministic reproducible experiments and structured event logging — **is**
>    implemented and verified, and this document claims only that.

---

## Project Details Used for This Document

| Item | Current information (verified) |
|---|---|
| Project | QuantumSigGuard — Quantum-Inspired Cyber Threat Detection for Digital Signature Security |
| SIH Problem Statement | SIH26141 |
| Organization | Egreen Quanta LLP |
| Theme | Security |
| Core focus | Teleportation-based Quantum Digital Signatures |
| Implementation language | Python 3.10+ (developed/verified on 3.14.7) |
| Runtime dependency | NumPy only (`numpy>=1.24`) |
| Detection approach | Two-layer statistical + Pauli-measurement threshold rules; **no AI/ML** |
| Quantum execution | Exact classical simulation (state vectors / density matrices, ≤ 3 qubits per register) |
| Real quantum hardware | **None — not used, not claimed** |
| Dataset | **No external dataset** — all observations simulation-generated from a seeded protocol |
| Core threat scenarios | Forgery, impersonation, replay, unauthorized verification, quantum-channel manipulation |
| Key operations | Bell-state/teleportation simulation, Pauli corrections Z^m1 X^m2, projective measurements, verification, attack analysis |
| Interface | Terminal CLI (`qsentinel-demo` / `python -m qsentinel.cli`) + JSON/Markdown reports |
| AI/ML | Excluded by requirement and by construction |

---

## Executive Summary

- The prototype demonstrates a **simulation-based Quantum Digital Signature security framework**:
  Bell-state entanglement, teleportation, Pauli corrections, projective measurement, signature
  verification, five attack scenarios and two deterministic threshold-based detectors. It uses
  **no AI/ML**, per SIH26141.
- Its primary security objective is to protect the **integrity and authenticity of digital
  signatures** against forgery, impersonation, replay, unauthorized verification and simulated
  quantum-channel manipulation — and to make each detection decision explainable by measurement
  statistics and fixed thresholds.
- The critical security boundary is **between the trusted protocol/detection logic and all
  untrusted inputs** (message/attack configuration). This is enforced structurally: configuration
  dataclasses validate every value at construction, are immutable at runtime (`frozen`), and are
  the single source of truth for all thresholds (`qsentinel/config.py`).
- The simulated protocol itself implements replay protection (nonce cache), an authorisation set
  for verification, coverage/completeness checks and structured per-transaction security-event
  export (`results/scenarios.json`) — all covered by a 73-test suite.
- Web-scale controls (authenticated RBAC, managed secrets, TLS, CORS/CSRF, rate limiting, hardened
  containers, SIEM/audit infrastructure, backups) do **not exist and are not claimed**, because the
  implementation has **no web surface**. They are listed as future hardening only if/when a service
  layer is introduced.
- The prototype must **not** be represented as a production quantum cryptographic service or as
  having been validated on real quantum hardware.

---

# 1. Overview and Scope

## 1.1 Purpose

This document describes the security architecture, access-control posture, threat model, data
protection approach and current limitations of the QuantumSigGuard prototype for SIH 2026: a
teleportation-based QDS threat-detection framework that performs quantum distribution simulation,
teleportation, Pauli corrections, projective measurement and statistical/threshold-based
threat classification with **no AI/ML**.

## 1.2 In Scope

- QDS simulation logic (`qsentinel/quantum`, `qsentinel/protocol`).
- Signing and verification operations (`sender`, `verifier`, `freshness`).
- Simulated quantum-state/measurement information.
- Attack-simulation inputs (`qsentinel/attacks`).
- Statistical + Pauli-measurement detection logic (`qsentinel/detection`).
- Verification thresholds and configuration (`qsentinel/config.py`).
- Protocol-level authorisation and replay controls.
- Security-event capture and export (`qsentinel/reporting`, `results/`).
- Source code, dependency and configuration integrity.
- Prototype (local CLI) deployment environment.

## 1.3 Out of Scope

- Real QKD infrastructure, physical quantum channels, entangled-photon generation or quantum
  processing units.
- Hardware Security Modules and production private-key management.
- Enterprise identity federation, certificate authority infrastructure or formal QDS certification.
- Production replacement of RSA/ECC signing systems.
- Web application / API security **beyond what exists** (there is no web surface today).
- Physical attacks on quantum hardware; nation-state-level certification; SLA/HA/DR guarantees.

---

# 2. Assets and Data Classification

| Asset | Classification | Security reason |
|---|---|---|
| Public SIH problem statement | **Public** | Intended for challenge participants |
| Project description / README | **Public** | Suitable for SIH presentation |
| Architecture & math documentation | **Internal** | Reveals implementation structure |
| Application source code | **Internal** | Unauthorized modification could alter verification behaviour |
| Quantum/QDS simulation logic | **Internal** | Core implementation |
| Attack-simulation logic | **Internal** | Misuse could undermine demonstrations or testing |
| Verification thresholds & configuration | **Internal** | Unauthorized modification changes detection outcomes → **validated, immutable at runtime** |
| Simulated signing keys / transaction material | **Internal** | Integrity and impersonation risk **within the simulation**; never real keys |
| Measurement/statistical output | **Internal** | Contains security-test results |
| Security-event records (`results/*.json`) | **Confidential** | May reveal attack attempts / internal behaviour |
| Authentication secrets, API credentials | **N/A** | No accounts, credentials or API exist |
| Production signing keys | **Not claimed** | Would require HSM-grade key management |

**Key distinction (enforced in docs/`README`):** the simulated per-transaction key and signature
material are *experiment data*, not real cryptographic key material. They are generated by seeded
RNG, kept in memory/JSON for the session and never presented as production secrets.

---

# 3. Threat Model

## 3.1 Trust Boundaries

```text
Operator (trusted local user)
   │  CLI arguments / config
   ▼
Input validation layer  (config __post_init__ + CLI range checks)
   │  validated ExperimentConfig (frozen)
   ▼
QDS Protocol Engine  (sender → channel → verifier)
   │
   ▼
Detection Engine  (statistical + Pauli layers)
   │
   ▼
Results / security-event export (JSON + Markdown)
```

Every externally-supplied value (message size, attack key, rates, trials, thresholds in config
files) crosses the validation boundary before touching protocol logic. There is **no remote trust
boundary** today — no network input path exists.

## 3.2 Likely Threat Actors

Within the simulator: forgers, impersonators, replay attackers, unauthorized verifiers and
channel manipulators (each a modelled scenario). Around the tool itself: a local adversary who can
modify source/config/files; and a compromised dependency or environment. Public API abusers are
**not applicable** (no public interface).

## 3.3 STRIDE Threat Analysis (with implemented status)

| STRIDE | Prototype-specific threat | Effect | Status / mitigation |
|---|---|---|---|
| **Spoofing** | Impersonating the signer/verifier in the protocol | Unauthorized signature acceptance | **Implemented** — impersonation scenario; identity bound to key via verification mismatch |
| **Spoofing** | Stealing application credentials | Unauthorized system access | **N/A** — no accounts/credentials exist |
| **Tampering** | Changing signature / channel data | Invalid signature accepted; manipulated measurements | **Implemented** — forgery + channel-manipulation scenarios and both detectors |
| **Tampering** | Modifying thresholds/config files | Distorted detection outcomes | **Partial** — validated, immutable-at-runtime config, single source of truth; no OS-level file ACLs (single-user local tool) |
| **Repudiation** | Denying an experiment/configuration run | Reduced accountability | **Implemented** — per-transaction security-event export with attack, nonce, signals, thresholds, verdicts |
| **Information Disclosure** | Leaking logs/simulation keys | Unauthorized use | **Partial** — logs are structured and local; no audit-store access control (single-user) |
| **DoS** | Excessive simulation/requests | CPU/memory exhaustion | **N/A** in CLI (bounded locally); rate limits **apply only if an API is added** |
| **Elevation of Privilege** | Normal user changes security settings | Security configuration altered | **N/A** — single-user CLI; no role hierarchy. Protocol-level authorisation is modelled in-simulation |

## 3.4 Project-Specific Security Risks

### Signature Forgery — implemented detection
An attacker signs with a guessed key (`guess_accuracy = 0.5`). Wrong guesses are eigenstates of the
wrong Pauli operator; the verifier's own-basis measurement then returns a random ±1, so mismatch
becomes visible. Measured: 100% detection by both layers (see `docs/results.md`).

### Impersonation — implemented detection
An attacker submits a *well-formed* signature bound to their own key and relabels the sender.
Mismatch concentrates exactly on positions where the two keys differ. Measured: 100% detection.

### Replay Attack — implemented detection
The verifier keeps a `ReplayCache` of accepted nonces (`freshness.py`, cache size 512). A replay is
rejected because `freshness_ok == False`, independently of the quantum data. Measured: 100%
detection by the statistical layer (and correctly 0% by the measurement layer, which by design is
blind to it — `docs/detection.md`).

### Unauthorized Verification — implemented detection
Verification is gated by an `authorised_entities` set; the verifier reports
`unauthorised verifying entity`, and the statistical layer raises its `authorisation` signal.
Measured: 100% detection.

### Quantum-Channel Manipulation — implemented detection
The channel-manipulation scenario injects Pauli errors on copies, forges classical teleportation
bits (wrong Pauli correction → residual Pauli), drops copies (coverage shortfall) and disturbs the
entanglement witness. Measured: 100% detection. The four disturbance channels are scored separately
in `channel_manipulation.py` because they are *not* equally powerful (classical-bit tampering flips
an eigenvalue only half the time).

### Dataset Tampering
**N/A / substitute control.** No external dataset is used. The equivalent risk — a modified
evaluation producing misleading metrics — is addressed by **deterministic seeding** (one top-level
seed drives all RNG), immutable config, and `results/config.json` recording the full configuration
alongside every result, so any claimed result is reproducible byte-for-byte.

### Model Poisoning
**Not applicable** — no learned model. The equivalent concern is **algorithm/configuration
poisoning** (thresholds, attack parameters, sample sizes). Mitigated by: thresholds fixed in
`DetectionConfig` and never fitted; validation in `__post_init__`; and the test suite locking
behaviour.

### Adversarial Inputs
Mitigated by **strict validation at every input boundary**:
- `ProtocolConfig`, `ChannelConfig`, `DetectionConfig.__post_init__` reject out-of-range values
  (thresholds outside `[0,1]`, `parity_group_size > copies_per_bit`, `sign_bit ∉ {0,1}`, etc.).
- CLI validates trial counts (`1..10000`) and group sizes (`≥ 1`); unknown scenarios raise
  `KeyError`; malformed numeric lists fail fast.
- Attack constructors validate `guess_accuracy`, fractions etc. in `[0,1]`.

### API Abuse
**N/A today** — no API exists. If a web service is added later, authentication, authorization,
rate limits and input-size limits must be introduced before exposure (see §13 roadmap).

---

# 4. Authentication

**No user authentication exists and none is needed in the current implementation** — the tool is a
local, single-operator CLI. Any statement of authentication "TBD" is replaced by: **N/A (no
accounts)**. If the prototype is later wrapped in a web service:

- authenticate before protected actions; Argon2id/bcrypt hashing; never store plaintext passwords;
- short-lived sessions/tokens that carry no secret QDS material;
- MFA for administrators; rate-limited logins; no username-enumeration oracle;
- keep any OAuth/OIDC credentials server-side and out of the repository.

## 4.1 Demo Credentials

**N/A** — no accounts. (`run_demo.py` is an unauthenticated local example; nothing is exposed
remotely.)

---

# 5. Authorization and Access Control

## 5.1 In the implemented prototype

There is **no application role system** (single local operator). What *is* implemented is
**protocol-level authorization**, modelled inside the simulator:

- `QDSSession` owns an `authorised_entities` set (default `{sender, verifier}`) and hands it to
  every attack context and the detection input (`session.py:91`, `build_input`).
- The `authorisation` statistic (`statistical.py:141`) and the verifier's
  `unauthorised verifying entity` reason (`verifier.py:241`) jointly reject transactions whose
  entity is not authorized.

| Resource / action (in-simulation) | Authorised entity | Unauthorised entity |
|---|:---:|:---:|
| Submit/verify a signed transaction | Allowed | Rejected (authorisation signal) |
| Reuse an accepted nonce | Rejected (replay signal) | Rejected |
| Run CLI `scenarios`/`evaluate` etc. | Local operator only | N/A (no remote access) |
| Modify thresholds/config | Single operator, file-level | N/A |

## 5.2 Recommended target matrix — only if a web/API layer is added

| Resource / Action | Admin | Analyst | Demo/Viewer |
|---|:---:|:---:|:---:|
| View results | ✓ | ✓ | ✓ |
| Run verification / approved scenarios | ✓ | ✓ | Optional (read-only preferred) |
| Modify thresholds | ✓ | ✗ | ✗ |
| View security-event logs | ✓ | Limited | ✗ |
| Manage datasets/config | ✓ | Limited | ✗ |
| Manage accounts/secrets | ✓ | ✗ | ✗ |

Least privilege: deny-by-default, separate users from configuration, prevent demo accounts from
changing security settings. **Not implemented today because there are no such surfaces.**

---

# 6. Data Protection

## 6.1 Data in Transit

**N/A** — the tool never opens a socket; all data stays on the local host. If deployed as a service
later: HTTPS with trusted certificates, redirect plain HTTP, do not directly expose backend ports.

## 6.2 Data at Rest

Persisted artifacts are plain JSON under `results/` (config, evaluation, sweeps, scenario events).
They contain **no personal data and no secrets**. Best practice already followed:

- `results/config.json` records the full configuration with every result (reproducibility).
- Generated artifacts are reproducible from seed + code (`scripts/generate_report.py`).

If a database is introduced later: restricted credentials, non-public backups, OS-level protection
for confidential logs.

## 6.3 Secrets Management

**There are no secrets.** The repo requires no API keys, tokens, credentials or environment
variables (runtime dependency is NumPy only). Verified by a source scan for
password/secret/credential/token/private-key patterns (§13.1). Therefore:

- No API keys in source code — **vacuously satisfied**.
- No credentials in `.git` history — **none exist** (see §13.1).
- `.env` / `.env.example` — **not needed**; a future service layer should add `.env.example` with
  variable names only.

## 6.4 Anonymization

**N/A** — no personal data is collected or stored.

## 6.5 Retention and Deletion

`results/` files are regenerable artifacts; deleting them is always safe (no state loss beyond
regenerable reports). No formal retention policy exists; a service deployment should define one for
audit records.

---

# 7. Application Security

## 7.1 Input Validation — **Implemented**

Verified controls (`qsentinel/config.py`, `qsentinel/cli.py`, attack constructors):

| Input | Rule | Where |
|---|---|---|
| Thresholds (mismatch, QBER, per-basis, distance, correlator, parity) | `0.0 <= v <= 1.0` | `DetectionConfig.__post_init__` |
| Decoh/tamper/loss rates | `0.0 <= v <= 1.0` | `ChannelConfig.__post_init__` |
| `message_length`, `copies_per_bit`, `witness_pairs`, `parity_group_size` | positive; `group <= copies`; `sign_bit ∈ {0,1}` | `ProtocolConfig.__post_init__` |
| `seed`, replay cache | `cache >= 1` | `DetectionConfig.__post_init__` |
| CLI trials | `1..10000` | `cli._parse_trials_safe` |
| CLI group sizes | positive integers | `cli.command_group_sweep` |
| Unknown scenario | `KeyError` | `session.run_scenario` |

Failures are loud (`ValueError`/`SystemExit`), never a silent change of algorithm behaviour.

## 7.2 Output Encoding / XSS

**N/A** — no browser rendering. Console output is plain text/tables; exported reports are
JSON/Markdown containing only program-generated values.

## 7.3 File Upload Security

**N/A** — there are no file uploads.

## 7.4 SQL Injection

**N/A** — there is no database.

## 7.5 CORS / CSRF

**N/A** — no web server, no browsers, no cookies.

## 7.6 Rate Limiting

**N/A / Planned-future.** Local CLI runs are resource-bounded by the operator. If a web service is
added, rate-limit login, verification, attack simulation and any expensive computation.

## 7.7 Dependency Security

**Partial.**

- Runtime dependency surface is minimal: **NumPy only** (`requirements.txt`: `numpy>=1.24`;
  `pyproject.toml` same).
- Pinning: a version *floor* is declared, but there is **no lockfile** and **no automated
  vulnerability scanner**. Pin/lock and scan before any wider distribution.

---

# 8. Model and Algorithm Security

## 8.1 No AI/ML Classification — **Implemented by design**

There is no trained model, no weights, no training/inference split, and no learned threshold. Every
detection decision is a deterministic comparison of measured protocol statistics against fixed,
documented thresholds (`docs/math.md`, `docs/detection.md`). This satisfies the SIH constraint that
detection use quantum/statistical principles rather than AI/ML.

## 8.2 Quantum-Inspired vs Real Quantum Hardware — **honest boundary**

The correct description, used throughout the repo docs:

> A classical software simulation / quantum-inspired implementation of teleportation-based QDS
> security concepts.

It does **not** claim real quantum channels, entangled-photon transmission, production QKD,
hardware-level information-theoretic security, or any quantum computational advantage.

## 8.3 Algorithm Integrity — **Implemented mitigations, no cryptographic release signing**

Integrity-sensitive components (protocol, basis operations, Pauli corrections, verification logic,
thresholds, attack parameters) are protected by:

- **Single source of truth** for every threshold (`qsentinel/config.py`; PRD requires no
  duplication) — `docs/prd-traceability.md`;
- **Immutable-at-runtime** frozen config dataclasses;
- a **73-test suite** (`python3 -m unittest discover -s tests`) that locks expected behaviour,
  including the Pauli-correction table, teleportation fidelity ≈ 1, Bell correlators and every
  detector signal;
- **deterministic reproducibility** via a single top-level seed and `results/config.json`.

Not present (future work): cryptographic release hashes / code signing.

## 8.4 Data / Dataset Validation

**N/A with substitute.** No external dataset. "Validation" is: seeded, reproducible generation;
config recorded beside results; attack/scenario keys validated; no hidden randomness.

## 8.5 Reproducibility — **Implemented**

Every experiment records: seed, protocol/channel/detection configuration, attack type, trials,
thresholds, per-signal values, verdicts and runtime — i.e. `results/config.json`,
`results/evaluation.json`, `results/scenarios.json`. Rerunning with the same seed reproduces the
report (verified during development).

---

# 9. Infrastructure and Deployment Security

## 9.1 Local Demo — current deployment

- The tool binds **nothing** to a network; it runs as a normal local process (no debug ports, no
  listeners).
- Runs under the invoking user's account; no privileged operations are performed.
- No `.env`, no confidential configuration, no network services to lock down.
- Console errors are the CLI's own messages; there is no remote-facing debug mode.

## 9.2 Container Hardening

**N/A today** — not containerized. If containerized later: minimal base image, non-root user,
pinned image tags, no secrets in the image, CPU/memory limits.

## 9.3 Environment Separation

**N/A today** — no environments. A future service should keep dev/demo/prod separate and never
share secrets between them.

## 9.4 Network Exposure

**N/A today** — nothing listens on a network. No firewall changes, no open ports.

## 9.5 Backups

**N/A / trivial.** All state is regenerable (code + seed). No database or user data exists.

---

# 10. Logging, Monitoring and Incident Response

## 10.1 Security-Event Logging — **Implemented**

The SIH expected solution explicitly includes security-event logging, and it is present:
`ScenarioResult.as_dict()` (`session.py:58`) exports, per transaction:

- scenario + attack title and `is_attack`/notes;
- verification outcome: `signature_valid`, `freshness_ok`, `authorisation_ok`, `reject_reason`,
  `mismatch_count`, `check_count`, `mismatch_rate`, failing checks;
- both detector verdicts and **every signal with its value, threshold, comparison and tripped
  state** (`detection_measures`);
- `elapsed_seconds` for benchmarking.

The `scenarios` CLI command and `scripts/generate_report.py` write this to
`results/scenarios.json` (and `scenarios.md`). This is a structured, per-event log — not yet a
tamper-evident / append-only audit store or a SIEM feed.

## 10.2 Information That Must Not Be Logged

**Policy, vacuously satisfied:** no passwords, tokens, API secrets or private signing keys exist to
log. Simulated per-transaction keys are experiment material, not credentials, and are never exported
into reports.

## 10.3 Monitoring / Alerting

**N/A today** (no service, no streams). For a future deployment, alert on repeated verification
failures, malformed input bursts, unauthorized admin attempts and configuration changes.

## 10.4 Prototype Incident-Response Procedure

For the local tool:

1. **Detect** — abnormal verdicts, failing tests, or anomalous files in `results/`.
2. **Contain** — stop running the tool; quarantine the environment.
3. **Preserve evidence** — keep `results/`, config and environment details.
4. **Investigate** — is the anomaly a modelled attack, an invalid input, a bug, or a
   tampered config/code?
5. **Remediate** — fix the defect; revert any modified code/config; rotate **nothing** (no secrets).
6. **Validate** — rerun the 73-test suite and the seeded report generator.
7. **Document** — record cause, impact, fix, prevention.

---

# 11. Privacy and Compliance Alignment

Alignment references only; **no certification or legal-compliance claim** is made.

## 11.1 Digital Personal Data Protection Act, 2023

**Low direct applicability** — the prototype processes no personal data (all data is simulated).
If identifiable data is ever introduced, apply purpose limitation, protection, controlled
retention, secure deletion and unauthorized-access controls.

## 11.2 Information Technology Act, 2000

General practice applies to any future public deployment (authorized access only, adequate security
measures). No network-facing component exists today.

## 11.3 OWASP

| OWASP area | Status in this prototype |
|---|---|
| Broken Access Control | Protocol-level authorisation implemented; app-level RBAC N/A (no accounts) |
| Cryptographic Failures | No real crypto/keys; simulation keys are ephemeral experiment data |
| Injection | No interpreter/SQL/HTML inputs to inject; config validated |
| Insecure Design | Threat model + trust boundaries documented here and in `docs/architecture.md` |
| Security Misconfiguration | Single source of truth, validated, immutable config; no remote debug/dev surface |
| Vulnerable Components | NumPy version floor declared; **no lockfile/scanner yet** (future) |
| Authentication Failures | N/A (no authentication) |
| Integrity Failures | Seeds + config-record + 73-test suite protect result/tool integrity |
| Logging Failures | Structured security events exported (see §10.1) |
| SSRF | N/A (no URL-fetching code) |

## 11.4 NIST CSF Alignment

- **Identify** — assets (§2), protocol components, threat model (§3).
- **Protect** — validation (§7.1), reproducible config, authorisation + replay controls (§5).
- **Detect** — the two detectors, freshness/authorisation rules, security-event export (§10.1).
- **Respond** — local incident procedure (§10.4).
- **Recover** — regenerate `results/` from code + seed; rerun tests.

This is an alignment mapping, not an attestation.

---

# 12. Known Limitations and Future Hardening

## 12.1 Current Limitations

- Quantum behaviour is **simulated**, not measured on real hardware; physical noise, decoherence
  timing and hardware imperfections are idealized (Pauli/tamper/loss model — `docs/limitations.md`).
- **No authentication, accounts, RBAC, MFA, TLS, rate limiting or monitoring** exists — because
  there is no web service; these become required only after a service layer is added.
- No **tamper-evident/append-only audit store**; events are structured JSON, not WORM logs.
- Config/threshold file edits are not blocked by OS-level ACLs (a local single-user tool).
- No **dependency lockfile or vulnerability scanner**.
- No cryptographic **release hashing/code signing** for the tool itself.
- No external/public dataset; results are simulator-generated (by design).
- The measurement-based (Pauli) layer **cannot** detect replay or unauthorized verification — this
  is a *documented protocol property*, reported honestly as measured false negatives
  (`docs/detection.md`, `docs/results.md`) rather than hidden.

## 12.2 Prioritized Hardening Roadmap

| Priority | Improvement | Status today |
|---|---|---|
| **P0** | Strict input/range validation | **Done** (§7.1) |
| **P0** | Single, immutable threshold configuration | **Done** (§8.3) |
| **P0** | Protocol-level replay + authorisation controls | **Done** (§3.4) |
| **P0** | Structured security-event export | **Done** (§10.1) |
| **P0** | Reproducible seeded experiments | **Done** (§8.5) |
| **P1** | Dependency lockfile + vulnerability scanning | Planned |
| **P1** | Release integrity hashes / signed artifacts | Planned |
| **P1** | Tamper-evident audit store (only if service layer) | Planned |
| **P2** | Authentication + RBAC + rate limiting (only if web API) | Planned-on-adoption |
| **P2** | HTTPS/TLS, hardened containers, monitoring (only if web API) | Planned-on-adoption |
| **P3** | HSM/KMS-backed key management | Not applicable in simulation; only for a real deployment |
| **P3** | Real quantum-backend validation | Future research |

---

# 13. Security Checklist and Evidence

## 13.1 Checklist

| Control | Status | Evidence |
|---|---|---|
| Teleportation-based QDS concept | **Implemented** | `qsentinel/protocol/teleportation.py` |
| Bell-state entanglement | **Implemented** | `qsentinel/quantum/states.py`, `gates.py` |
| Pauli correction / measurement | **Implemented** | `teleportation.py` (`_CORRECTION_TABLE`, `Z^m1 X^m2`) |
| Statistical threshold detection | **Implemented** | `qsentinel/detection/statistical.py` |
| Pauli-measurement detection | **Implemented** | `qsentinel/detection/pauli.py` |
| AI/ML excluded | **Implemented** | entire `qsentinel/detection` (fixed rules); `docs/architecture.md` |
| Forgery scenario | **Implemented** | `qsentinel/attacks/forgery.py`, `tests/test_attacks.py` |
| Impersonation scenario | **Implemented** | `qsentinel/attacks/impersonation.py` |
| Replay scenario + freshness cache | **Implemented** | `qsentinel/attacks/replay.py`, `protocol/freshness.py` |
| Unauthorized-verification scenario | **Implemented** | `qsentinel/attacks/unauthorized.py`, `session.authorised_entities` |
| Channel-manipulation scenario (4 disturbance channels) | **Implemented** | `qsentinel/attacks/channel_manipulation.py`, `channel.py` |
| Security-event logging | **Implemented** (JSON events; not a WORM audit store) | `session.ScenarioResult.as_dict`, `reporting/export.write_json`, `results/scenarios.json` |
| Input validation (config/CLI/attacks) | **Implemented** | `config.py` `__post_init__`, `cli._parse_trials_safe` |
| Deterministic reproducibility | **Implemented** | one seed; `results/config.json` |
| No secrets / credentials anywhere | **Verified** | source scan (below); NumPy-only runtime |
| Dataset / dataset checksum | **N/A** (no external dataset; seeded simulation instead) | `results/config.json` |
| Authentication | **N/A** (no accounts) | — |
| MFA / RBAC / admin roles | **N/A** (no accounts); protocol authorisation implemented | `session.py:91`, `verifier.py:241` |
| HTTPS/TLS, CORS, CSRF, rate limiting | **N/A** (no web server) | — |
| File uploads / SQL injection | **N/A** (no uploads, no database) | — |
| Dependency pinning | **Partial** (floor only, no lockfile) | `requirements.txt`, `pyproject.toml` |
| Dependency vulnerability scanning | **Planned** | — |
| Containers / backups / monitoring | **N/A today** (local CLI; regenerable state) | — |
| Incident-response procedure documented | **Implemented (documentation)** | §10.4 |
| Real-quantum / production-CSR claims | **Explicitly not claimed** | §8.2, `docs/limitations.md` |

## 13.2 Evidence Map (file → control)

| Control | File(s) |
|---|---|
| Threshold & config source of truth | `qsentinel/config.py` |
| Validation invariants | `qsentinel/config.py` (`__post_init__` × 3) |
| Immutable config | `frozen=True` dataclasses, `config.py` |
| Replay cache | `qsentinel/protocol/freshness.py` |
| Authorisation set | `qsentinel/session.py:91` |
| Authorisation/replay signals | `qsentinel/detection/statistical.py:133-148` |
| Reject reasons | `qsentinel/protocol/verifier.py:228-256` |
| Event record | `qsentinel/session.py:58-73` |
| Event export | `qsentinel/reporting/export.py`, `scripts/generate_report.py` |
| No-secrets scan | `grep -rn "password\|secret\|token\|credential\|private key" qsentinel/` → **no matches** (only doc strings using the word "secret" for the simulated key concept) |
| Behaviour lock | `tests/` (73 tests) |
| Reproducibility | one seed (`config.DEFAULT_SEED`), `results/config.json` |

A scan for credential patterns returns no matches: the matched strings in the repository are
docstring uses of the word "secret" describing the *simulated* signing key, not stored credentials.

---

# Final Security Position

QuantumSigGuard is a **research and demonstration security framework for teleportation-based QDS
threat detection**. It applies quantum-inspired protocol operations and deterministic statistical
thresholding to detect forgery, impersonation, replay, unauthorized verification and channel
manipulation, with **no AI/ML** — and it closes the loop with structured, reproducible security-event
output and behaviour-locking tests.

Its principal strengths for the SIH prototype stage are: detection decisions are **explainable**
down to individual measurement statistics and thresholds (§8.1); results are **reproducible** from a
single seed (§8.5); inputs are **validated** at every boundary (§7.1); the simulated protocol itself
enforces **replay protection and authorisation** (§5.1); and the project states its limits honestly
(simulation-only, no real quantum hardware, measurement-blind spots on replay/unauthorized —
§12.1).

Simulation security and production application security remain separate concerns. Because the
current artifact has **no web surface, no accounts, no secrets and no network exposure**, the
web-era controls are marked **N/A** instead of being overclaimed as "planned"; they become
requirements only when a service layer is introduced. This distinction keeps the submission
technically credible: it demonstrates the required **QDS security and attack-detection concept**
without overstating production or real-quantum security guarantees.