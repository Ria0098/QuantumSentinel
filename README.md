# QuantumSigGuard

Quantum-inspired cyber threat detection for **teleportation-based Quantum
Digital Signatures** (Smart India Hackathon 2026, S. No. 26141).

A pure-NumPy prototype that simulates the full QDS flow — sender signing,
quantum teleportation, a noisy quantum+classical channel, the verifier, **five
attack simulations**, and **two non-AI/ML detection layers** — then evaluates
them with reproducible, seeded experiments.

```
QuantumCore (exact state vector / Pauli bases / Bell pairs / teleportation)
  → Sender signs (X/Z key-dictated eigenstates)
  → QuantumChannel distributes (teleport + noise model + attack disturbances)
  → Verifier checks (per-copy, cat-state parity, witness, coverage, freshness)
  → Detection: StatisticalDetector  +  PauliMeasurementDetector  → verdict
  → Evaluation: confusion metrics, noise & amplification sweeps, reports
```

## Quick start

Requires CPython ≥ 3.10 and NumPy (no other dependencies).

```bash
cd ~/Desktop/QuantumSentinel
python3 run_demo.py                # comparison table + detailed report + metrics
python3 -m qsentinel.cli scenarios # all six scenarios side by side
python3 -m qsentinel.cli demo forgery   # full detail for one scenario
```

Install as a package (optional):

```bash
pip install -e .
qsentinel-demo scenarios
```

## Command line

```
qsentinel scenarios                run each scenario once (comparison table)
qsentinel demo [scenario]          full per-scenario report
qsentinel evaluate --trials N      controlled experiment with 95% CIs
qsentinel noise-sweep              detector behaviour vs channel decoherence
qsentinel group-sweep              detector behaviour vs amplification group size
```

JSON / Markdown exports: `--output path.json` writes machine-readable results.

## Browser dashboard (optional)

```bash
pip install -e ".[web]"          # streamlit + pandas + altair
streamlit run streamlit_app.py   # http://localhost:8501
```

Three pages: Overview (pre-generated `results/` plus sweep charts), Scenario lab
(run any attack, inspect both detectors live), and a configurable Evaluation run
with JSON/CSV export. Pure view layer over the same engine - no simulation logic
in the UI. The UI lives in `ui/` (design tokens + Altair theme +
components); pages in `app_pages/`. Dark / light themes are both supported
(`.streamlit/config.toml`).

## Reproducing the report

```bash
python3 scripts/generate_report.py --trials 200 --sweep-trials 50   # -> results/
python3 scripts/benchmark.py --trials 20
python3 -m unittest discover -s tests                               # test suite
```

## Headline results (seed 20260101, L=8, n=4, g=2)

| detector | detection rate | false-alarm rate |
| -------- | -------------- | ---------------- |
| statistical | 1.000 | 0.000 |
| pauli measurement | 0.600 | 0.000 |

The Pauli layer's 0.600 is by design: replay and unauthorised verification are
quantum-invisible (the transcript is bit-identical to a legitimate run) and are
caught only by the classical freshness/authorisation rules in the statistical
layer.  The method comparison table therefore reports an honest split rather
than a convenient 100%.  Details: `docs/results.md`, `docs/detection.md`.

## Documentation

* `docs/architecture.md` - components and layering rules
* `docs/math.md` - the QDS, teleportation, amplification and detection math
* `docs/attacks.md` - the five attack scenarios and the threat model
* `docs/detection.md` - the two detection layers and why they disagree
* `docs/results.md` - measured detection, noise and group-size results
* `docs/security.md` - security & access document (threat model, controls, evidence map)
* `docs/frontend.md` - interface & frontend specification (CLI/console/export layer, no web stack)
* `docs/technical_architecture.md` - full technical architecture with measured values
* `docs/limitations.md` - honest scope and engineering caveats
* `docs/prd-traceability.md` - requirement-to-implementation mapping
* `docs/feature-backlog.md` - feature ticket list with statuses corrected to match the repo
* `results/` - machine-readable artifacts produced by `generate_report.py`

## Repository layout

```
qsentinel/
  quantum/      exact state-vector engine, gates, bases, measurement, Bell states
  protocol/     sender, channel, verifier, freshness cache, data structures
  attacks/      five attack simulations + benign baseline + registry
  detection/    statistical and Pauli-measurement detectors + engine
  evaluation/   confusion metrics, runner, noise & group sweeps
  reporting/    console rendering and JSON/Markdown export
  session.py    end-to-end orchestrator
  config.py     single source of truth for thresholds and structure
  cli.py        interactive command line
scripts/        benchmark, evaluation, full report generation
tests/          unittest suite (73 tests)
run_demo.py     one-command demo
```