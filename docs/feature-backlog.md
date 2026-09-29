# Feature Backlog — SIH26141 QuantumSigGuard (corrected against the codebase)

This is the feature ticket list, corrected so that every ticket's status reflects the
actual repository rather than the template's "mostly Not Started" state.  Statuses were
assigned by verifying the named code below, not by intent.  Where a feature exists only
in CLI/console form or as the optional local web dashboard (see the `[web]` extra and
`streamlit_app.py`), that is stated explicitly.

**Facts used throughout.**  Repo: `qsentinel/`, Python 3.14.7, numpy 2.5.3.  No web/API
server, no database, no Docker, no Qiskit/real hardware, no AI/ML learners.  The
"backend/frontend" boundary is `QDSSession` + CLI (`qsentinel/cli.py`) + reporting
(`qsentinel/reporting/`), plus an optional read-only Streamlit view layer
(`ui/`, `app_pages/`, `web_helpers.py`).  Measured results were produced with seed
`20260101`, 200 trials/attack (1200 total): statistical detector 1.000 [0.996,1.000]/FAR
0.000; Pauli 0.600 [0.569,0.630]/FAR 0.000; ~11 ms/transaction; 73 tests green.

---

## 1. Account in this backlog

```
# Backlog Team:QuantumSentinel Project:SQDS Type:feature Rank:CSV-id
## Feature Backlog (CSV export) + GUI panel
This backlog owns the QDS prototype capability (SIH-25182): quantum core, teleportation,
threat simulation, detection, evaluation, CLI/console interface and documentation.
```

## 2. Correct backlog assumptions

Replace the template's placeholder rows with the verified stack:

| Field | Was (template) | Correct (repo) |
| --- | --- | --- |
| Backend runtime | web service | single-process Python package (`qsentinel/`) |
| Backend interface | REST/HTTP | CLI commands (`demo`, `scenarios`, `evaluate`, `noise-sweep`, `group-sweep`) via `QDSSession` |
| Data storage | database | JSON files under `results/` (`write_json`, `generate_report.py`) |
| Data generation | 20,000 tx | 1200-trial evaluation, 200/attack, seed `20260101` (deterministic) |
| Frontend | browser screens | ANSI console tables/bars + JSON/Markdown export (`docs/frontend.md`) |
| Quantum backend | real QPU | exact state-vector simulation (numpy); no real-hardware claims |
| AI/ML | model | none — fixed-rule detectors only |

## 3. Corrected ticket list

Status shorthand: **Done** (verified in code), **Partial** (some acceptance criteria only),
**N/A** (not applicable to a CLI-only synchronous product), **Not Started** / **Won't**
(kept honestly).

### EP-01 Core QDS protocol

| ID | Title | Type | State | Estimate | Priority | Labels |
| --- | --- | --- | --- | --- | --- | --- |
| FT-001 | Deterministic simulation configuration | feature | **Done** | 1 SP | Must | deterministic, configurable |
| FT-002 | Bell-state generation and entanglement | feature | **Done** | 2 SP | Must | quantum |
| FT-003 | Quantum teleportation of a message state | feature | **Done** | 2 SP | Must | quantum |
| FT-004 | Pauli correction logic | feature | **Done** | 1 SP | Must | core |
| FT-005 | Projective verification (final measurement) | feature | **Done** | 2 SP | Must | quantum |

- **FT-001** `config.py` frozen dataclasses; seed `20260101`; every run reproducible; frozen config emitted to `results/config.json`. Validation in `__post_init__`.
- **FT-002** `quantum/states.py`, `quantum/gates.py` — exact state-vector Bell pair `(|00>+λ|11>)/√2`.
- **FT-003** `protocol/teleportation.py` — Bell, measurement, classical bits, reconstruction `Z^m1 X^m2`.
- **FT-004** `_CORRECTION_TABLE`, `(1,1)→Y (≡ ZX up to global phase)`.
- **FT-005** `protocol/verifier.py` — projective measurement in `v` basis; parities + witnesses.

### EP-02 Threat simulation

| ID | Title | Type | State | Estimate | Priority | Labels |
| --- | --- | --- | --- | --- | --- | --- |
| FT-006 | Simulate forgery (fundamental) | feature | **Done** | 2 SP | Must | attack |
| FT-007 | Simulate impersonation | feature | **Done** | 2 SP | Must | attack |
| FT-008 | Simulate replay | feature | **Done** | 2 SP | Must | attack |
| FT-009 | Simulate unauthorised verification | feature | **Done** | 1 SP | Must | attack |
| FT-010 | Simulate channel manipulation | feature | **Done** | 2 SP | Must | attack |

- All in `qsentinel/attacks/` with shared `Attack` base + registry; `ATTACK_ORDER` drives evaluation. **FT-010** also models four disturbance channels (`qsentinel/channel.py`).
- Measured 200/200 detection of forgery/impersonation/channel manipulation; replay & unauthorised quantum-invisible → caught only by classical rules (`docs/results.md`, `docs/detection.md`).

### EP-03 Detection engine

| ID | Title | Type | State | Estimate | Priority | Labels |
| --- | --- | --- | --- | --- | --- | --- |
| FT-011 | Mismatch statistics (cryptographic) | feature | **Done** | 2 SP | Must | non-AI |
| FT-012 | Configurable thresholds | feature | **Done** | 1 SP | Must | configurable |
| FT-013 | Outcome classification | feature | **Done** | 2 SP | Must | core |
| FT-014 | Explain threat-detection evidence | feature | **Done** | 2 SP | Must | evidence |

- **FT-011/012** `detection/statistical.py`; thresholds single-sourced in `DetectionConfig` (mismatch 0.05, qber 0.02, per-basis 0.05, distribution-distance 0.20, correlator/parity 0.90, replay cache 512).
- **FT-013** `DetectionEngine` + `DetectionResult.verdict` (`THREAT`/`LEGITIMATE`, `ACCEPT`/`REJECT`).
- **FT-014** per-signal tables in `reporting/render.py` show rule + measured value + threshold + tripped state; no AI claim made anywhere.

### EP-04 Data & experiment pipeline

| ID | Title | Type | State | Estimate | Priority | Labels |
| --- | --- | --- | --- | --- | --- | --- |
| FT-015 | Experiment result schema | feature | **Done** | 2 SP | Must | schema |
| FT-016 | Save experiment results | feature | **Done** | 2 SP | Must | persistence |
| FT-017 | Export results | feature | **Done** | 1 SP | Must | export |
| FT-018 | Validate experiment inputs | feature | **Done** | 1 SP | Must | validation |

- **FT-015** `TrialRecord`, `EvaluationResult.summary()`, `ScenarioResult.as_dict` (typed dataclasses, no fabricated values).
- **FT-016/017** JSON on disk (`results/*.json`), `reporting/export.py` (`write_json`, `scenario_to_markdown`), `scripts/generate_report.py`. No database — documented as by-design (storage = results bundle).
- **FT-018** `config.py __post_init__` (3 configs), CLI range checks, unknown attack → `KeyError`; negative tests in `test_config.py`, `test_cli.py`.

### EP-05 Backend / service layer

| ID | Title | Type | State | Estimate | Priority | Labels |
| --- | --- | --- | --- | --- | --- | --- |
| FT-019 | Protocol execution service | feature | **Done (in-process)** | 2 SP | Must | service |
| FT-020 | Attack execution service | feature | **Done (in-process)** | 2 SP | Must | service |
| FT-021 | Detection integration | feature | **Done** | 1 SP | Must | integration |
| FT-022 | Backend error conventions | feature | **Done (CLI-level)** | 1 SP | Should | errors |

- **FT-019/020** the "service boundary" is `QDSSession` + CLI subcommands; no HTTP API exists (documented in `docs/frontend.md`). A web service wrapper would be new work.
- **FT-021** every scenario runs `DetectionEngine` before returning; verdict in the result.
- **FT-022** errors are surfaced as `ValueError`/`KeyError`/`argparse SystemExit` with field-specific messages; no tracebacks in normal flows.

### EP-06 Frontend / interface

| ID | Title | Type | State | Estimate | Priority | Labels |
| --- | --- | --- | --- | --- | --- | --- |
| FT-023 | Experiment configuration screen | feature | **Done (CLI)** | 2 SP | Must | ui, cli |
| FT-024 | QDS protocol workflow view | feature | **Done (CLI)** | 2 SP | Must | ui, cli |
| FT-025 | Measurement-statistics visualisation | feature | **Done (console)** | 2 SP | Must | ui, cli |
| FT-026 | Threat verdict panel | feature | **Done (console)** | 2 SP | Must | ui, cli |
| FT-027 | Loading / empty states | feature | **N/A** | 1 SP | Should | ui |
| FT-028 | Actionable frontend errors | feature | **Done (CLI)** | 1 SP | Should | ui, cli |

- The "frontend" is the console/reporting layer (`docs/frontend.md`). **FT-023** CLI flags + presets (`clean`/`noisy`/`degraded`); **FT-024** protocol-stage blocks in `render_scenario`; **FT-025** per-basis measurement + signal tables; **FT-026** verdict banner with supporting values + thresholds; **FT-028** specific messages like `error: expected a positive integer, got 'x'`.
- **FT-027** N/A: no async loading (synchronous CLI); empty states render `(no rows)`; browser screens, charts and duplicate-submission prevention are future web work, not applicable to a CLI.

### EP-07 Evaluation & benchmarking

| ID | Title | Type | State | Estimate | Priority | Labels |
| --- | --- | --- | --- | --- | --- | --- |
| FT-029 | Evaluation experiment matrix | feature | **Done** | 2 SP | Must | evaluation |
| FT-030 | Benchmark vs classical baseline | feature | **Partial** | 2 SP | Must | comparison |
| FT-031 | Attack-detection performance | feature | **Done** | 2 SP | Must | metrics |
| FT-032 | Computational performance | feature | **Done** | 1 SP | Should | performance |
| FT-033 | Benchmark summary view | feature | **Done (console)** | 1 SP | Should | ui, cli |

- **FT-029** `evaluation/runner.py run_evaluation` — benign + 5 attacks, configurable trials, no pre-filled results.
- **FT-030 Partial:** the statistical layer is documented as the deterministic baseline comparator and results avoid any superiority claim, but there is no separate standalone "classical baseline algorithm" to benchmark against (`docs/results.md` §10.5 discusses two baseline concepts). Honest gap.
- **FT-031** per-attack detection/FAR/accuracy + 95% Wilson CI for both detectors (`evaluation/metrics.py`, `results/evaluation.json`).
- **FT-032** `scripts/benchmark.py` wall-clock mean ~11 ms/tx over all scenarios; `elapsed_seconds` per run.
- **FT-033** console summary tables + JSON export (`render_evaluation`, `render_evaluation_table`); web charts N/A.

### EP-08 Security & reliability

| ID | Title | Type | State | Estimate | Priority | Labels |
| --- | --- | --- | --- | --- | --- | --- |
| FT-034 | Log security-relevant events | feature | **Done** | 2 SP | Must | security |
| FT-035 | Sanitise untrusted inputs | feature | **Done** | 1 SP | Must | security |
| FT-036 | Handle execution failures | feature | **Partial** | 1 SP | Should | reliability |

- **FT-034** `ScenarioResult.as_dict` event records written to `results/scenarios.json` (attack type + verdict; no sensitive data logged) — verified by repo credential scan.
- **FT-035** config `__post_init__` + CLI range validation; zero untrusted-input paths (no remote input at all).
- **FT-036 Partial:** validated inputs prevent most failures and `KeyboardInterrupt→exit 130`; but there is no try/except wrapper that records a structured error record and lets a batch run continue after a mid-run failure.

### EP-09 Testing & deployment

| ID | Title | Type | State | Estimate | Priority | Labels |
| --- | --- | --- | --- | --- | --- | --- |
| FT-037 | Protocol unit tests | feature | **Done** | 2 SP | Must | testing |
| FT-038 | Attack/detector tests | feature | **Done** | 2 SP | Must | testing |
| FT-039 | End-to-end integration test | feature | **Done** | 2 SP | Must | testing |
| FT-040 | Reproducible local deployment | feature | **Done** | 2 SP | Must | packaging |
| FT-041 | Offline demo fallback | feature | **Done** | 2 SP | Must | demo |

- **FT-037** `tests/test_quantum.py`, `test_teleportation.py`, `test_protocol.py`.
- **FT-038** `test_attacks.py`, `test_detection.py` (incl. threshold behaviour) + legitimate-case coverage.
- **FT-039** `test_cli.py` drives `scenarios`/`demo`/`evaluate`; all five attack paths exercised; **73 tests green** (`python3 -m unittest discover -s tests`). Retry-path verification N/A offline.
- **FT-040** `pyproject.toml` + `requirements.txt`; editable install verified in a clean venv.
- **FT-041** pre-generated `results/` (seed `20260101`) + `run_demo.py`; fully offline.

### EP-10 Documentation

| ID | Title | Type | State | Estimate | Priority | Labels |
| --- | --- | --- | --- | --- | --- | --- |
| FT-042 | Document the math model | task | **Done** | 2 SP | Must | docs |
| FT-043 | Document the threat model | task | **Done** | 1 SP | Must | docs |
| FT-044 | README | task | **Done** | 1 SP | Must | docs |
| FT-045 | SIH demo script / walkthrough | task | **Done** | 1 SP | Must | demo |

- **FT-042** `docs/math.md`; **FT-043** `docs/attacks.md` + `docs/security.md`; **FT-044** `README.md`; **FT-045** three-minute demo path in `docs/frontend.md` (§2.3/§4.3) + `run_demo.py`.

### EP-11 Stretch (future)

| ID | Title | Type | State | Estimate | Priority | Labels |
| --- | --- | --- | --- | --- | --- | --- |
| FT-046 | Batch experiment runner | feature | **Done (absorbed)** | 3 SP | Could | script |
| FT-047 | Configurable noise models | feature | **Done (already in MVP)** | 3 SP | Could | quantum |
| FT-048 | Multi-threshold comparison | feature | **Partial** | 3 SP | Could | evaluation |
| FT-049 | Experiment history dashboard | feature | **Partial (read-only viewer)** | 3 SP | Could | web |
| FT-050 | Downloadable security report | feature | **Done (export)** | 2 SP | Could | export |
| FT-051 | Real quantum backend | feature | **Not Started (out of scope)** | 13 SP | Could | quantum |
| FT-052 | PostgreSQL persistence | feature | **Not Started (out of scope)** | 5 SP | Could | backend |
| FT-053 | Auth / access control | feature | **Not Started** | 5 SP | Could | security |
| FT-054 | Containerisation / deployment | task | **Not Started** | 3 SP | Could | devops |
| FT-055 | CI pipeline | task | **Not Started** | 2 SP | Could | devops |

- **FT-046 Done:** `scripts/run_evaluation.py`, `scripts/generate_report.py`, `evaluate --trials`, sweeps.
- **FT-047 Done:** `ChannelConfig(decoherence_rate, message_tamper_rate, loss_rate)` + presets `clean`/`noisy`(0.01)/`degraded`(0.05) + `noise-sweep`.
- **FT-048 Partial:** thresholds are configurable and validated, but there is no automated threshold-sensitivity sweep (easy follow-up).
- **FT-049 Partial:** the optional read-only Streamlit viewer (`streamlit_app.py` + `app_pages/` + `ui/`) renders the results bundle and live runs, but there is no persisted per-run experiment history.
- **FT-050 Done:** report bundle = `results/{config, evaluation, scenarios, noise_sweep, group_sweep}.json` + `scenarios.md`.
- **FT-051/052** depend on hardware/database infrastructure this prototype deliberately excludes (`docs/limitations.md`); kept honest.
- **FT-053** protocol-level authorisation exists (`session.py`, docs/security.md §5); no user accounts yet.
- **FT-055** tests run via the documented unittest command; no CI wiring.

## 4. Corrected dependency graph

Effectively complete: EP-01 → EP-02 → EP-03 → EP-04 → EP-05 holds; EP-06 is satisfied by the
CLI/reporting layer; EP-07→EP-10 are done.  Remaining owners of open edges: FT-030, FT-036,
FT-048 (Partial), FT-049 (Partial — read-only viewer), FT-053/054/055 (Not Started, stretch).

## 5. Corrected MVP scope

The MVP is **delivered**: EP-01..EP-04, EP-05(CLI form), EP-06(CLI form), EP-07, EP-08
(except FT-036+), EP-09, EP-10.  Only the explicitly marked Partial/Not-Started/web items
remain, and none blocks the demonstrable SIH deliverable.

## 6. Corrected risk list

| Risk | Likelihood | Impact | Status |
| --- | --- | --- | --- |
| Pauli detector blind to replay/unauthorised | Certain | Medium | Realised & honestly documented (DR 0.600 vs 1.000 statistical); classical rules close the gap |
| Overclaiming real-hardware/CSR applicability | Medium | High | Mitigated — docs explicitly exclude (`docs/limitations.md`) |
| Legal overclaim against AI/ML requirement | Low | High | Mitigated — no AI/ML; documented rationale |
| Reproducibility drift | Low | Medium | Mitigated — fixed seed + typed schema |
| Scope creep into web/API/DB | Medium | Medium | Deferred to FT-049/052/053/054 |

## 7. DoD

Unchanged (all tickets in MVP scope satisfy: code + tests green + docs updated + results
bundle regenerated).

## 8. Traceability

1:1 with implementations named above; detailed requirement mapping in `docs/prd-traceability.md`.

## 9. Corrected sprint plan (retrospective)

| Sprint | Planned | Result |
| --- | --- | --- |
| Sprint 1 | EP-01 core | Delivered |
| Sprint 2 | EP-02 + EP-03 | Delivered |
| Sprint 3 | EP-04 + EP-07 + CLI | Delivered |
| Sprint 4 | EP-08 + EP-09 + EP-10 | Delivered |
| Stretch | EP-11 + web items | Partial (046/047/050 done; 049/053/054/055 future) |

## 10. Corrected sprint review

All MVP epics accepted in-closing. Remaining backlog is stretch/web/deployment only.

## 11. Corrected CSV export

```csv
id,title,type,state,Estimate,Priority,Releases
FT-001,Deterministic simulation configuration,feature,Done,1,Must,2026.1.0
FT-002,Bell-state generation and entanglement,feature,Done,2,Must,2026.1.0
FT-003,Quantum teleportation of a message state,feature,Done,2,Must,2026.1.0
FT-004,Pauli correction logic,feature,Done,1,Must,2026.1.0
FT-005,Projective verification (final measurement),feature,Done,2,Must,2026.1.0
FT-006,Simulate forgery (fundamental),feature,Done,2,Must,2026.1.0
FT-007,Simulate impersonation,feature,Done,2,Must,2026.1.0
FT-008,Simulate replay,feature,Done,2,Must,2026.1.0
FT-009,Simulate unauthorised verification,feature,Done,1,Must,2026.1.0
FT-010,Simulate channel manipulation,feature,Done,2,Must,2026.1.0
FT-011,Mismatch statistics (cryptographic),feature,Done,2,Must,2026.1.0
FT-012,Configurable thresholds,feature,Done,1,Must,2026.1.0
FT-013,Outcome classification,feature,Done,2,Must,2026.1.0
FT-014,Explain threat-detection evidence,feature,Done,2,Must,2026.1.0
FT-015,Experiment result schema,feature,Done,2,Must,2026.1.0
FT-016,Save experiment results,feature,Done,2,Must,2026.1.0
FT-017,Export results,feature,Done,1,Must,2026.1.0
FT-018,Validate experiment inputs,feature,Done,1,Must,2026.1.0
FT-019,Protocol execution service,feature,Done (in-process),2,Must,2026.1.0
FT-020,Attack execution service,feature,Done (in-process),2,Must,2026.1.0
FT-021,Detection integration,feature,Done,1,Must,2026.1.0
FT-022,Backend error conventions,feature,Done (CLI-level),1,Should,2026.1.0
FT-023,Experiment configuration screen,feature,Done (CLI),2,Must,2026.1.0
FT-024,QDS protocol workflow view,feature,Done (CLI),2,Must,2026.1.0
FT-025,Measurement-statistics visualisation,feature,Done (console),2,Must,2026.1.0
FT-026,Threat verdict panel,feature,Done (console),2,Must,2026.1.0
FT-027,Loading / empty states,feature,N/A,1,Should,future
FT-028,Actionable frontend errors,feature,Done (CLI),1,Should,2026.1.0
FT-029,Evaluation experiment matrix,feature,Done,2,Must,2026.1.0
FT-030,Benchmark vs classical baseline,feature,Partial,2,Must,future
FT-031,Attack-detection performance,feature,Done,2,Must,2026.1.0
FT-032,Computational performance,feature,Done,1,Should,2026.1.0
FT-033,Benchmark summary view,feature,Done (console),1,Should,2026.1.0
FT-034,Log security-relevant events,feature,Done,2,Must,2026.1.0
FT-035,Sanitise untrusted inputs,feature,Done,1,Must,2026.1.0
FT-036,Handle execution failures,feature,Partial,1,Should,future
FT-037,Protocol unit tests,feature,Done,2,Must,2026.1.0
FT-038,Attack/detector tests,feature,Done,2,Must,2026.1.0
FT-039,End-to-end integration test,feature,Done,2,Must,2026.1.0
FT-040,Reproducible local deployment,feature,Done,2,Must,2026.1.0
FT-041,Offline demo fallback,feature,Done,2,Must,2026.1.0
FT-042,Document the math model,task,Done,2,Must,2026.1.0
FT-043,Document the threat model,task,Done,1,Must,2026.1.0
FT-044,README,task,Done,1,Must,2026.1.0
FT-045,SIH demo script / walkthrough,task,Done,1,Must,2026.1.0
FT-046,Batch experiment runner,feature,Done,3,Could,2026.1.0
FT-047,Configurable noise models,feature,Done,3,Could,2026.1.0
FT-048,Multi-threshold comparison,feature,Partial,3,Could,future
| FT-049,Experiment history dashboard,feature,Partial (read-only viewer),3,Could,future
FT-050,Downloadable security report,feature,Done,2,Could,2026.1.0
FT-051,Real quantum backend,feature,Not Started,13,Could,future
FT-052,PostgreSQL persistence,feature,Not Started,5,Could,future
FT-053,Auth / access control,feature,Not Started,5,Could,future
FT-054,Containerisation / deployment,task,Not Started,3,Could,future
FT-055,CI pipeline,task,Not Started,2,Could,future
```