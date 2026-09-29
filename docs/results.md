# Results

Produced by `scripts/generate_report.py` with the default seed `20260101` and
the default configuration (`L = 8`, `n = 4`, `witness_pairs = 8`,
`parity_group_size = 2`).  Raw artifacts: `results/config.json`,
`results/scenarios.json`, `results/evaluation.json`, `results/noise_sweep.json`,
`results/group_sweep.json`, `results/scenarios.md`.

## Method comparison (200 trials per scenario)

| detector | detection rate (95% CI) | false-alarm rate | accuracy |
| -------- | ------------------------ | ---------------- | -------- |
| statistical | **1.000** [0.996, 1.000] | **0.0000** | 1.000 |
| pauli measurement | **0.600** [0.569, 0.630] | **0.0000** | 0.667 |

Per-attack ground truth (statistical / Pauli detections out of 200):

| scenario | truth | statistical | Pauli | protocol rejects | mean E |
| -------- | ----- | ----------- | ----- | ---------------- | ------ |
| legitimate | benign | 0 | 0 | 0 | 0.0000 |
| forgery | attack | 200 | 200 | 200 | 0.2344 |
| impersonation | attack | 200 | 200 | 200 | 0.2656 |
| replay | attack | 200 | 0 | 200 | 0.0000 |
| unauthorized verification | attack | 200 | 0 | 200 | 0.0000 |
| channel manipulation | attack | 200 | 200 | 200 | 0.5000 |

The Pauli layer's `0.600` is **not an implementation defect** - it is the
measured consequence of the design: replay and unauthorised verification keep
the quantum transcript bit-identical to a legitimate run, so no
measurement-based detector can see them (see `docs/detection.md`).  The
statistical layer catches them via the classical freshness and authorisation
rules.

## Noise sweep (legitimate false-alarm behaviour)

Decoherence rate → statistical detection / statistical false alarm / Pauli
detection / Pauli false alarm (50 trials per point):

| p | stat detection | stat false alarm | pauli detection | pauli false alarm |
| - | -------------- | ---------------- | --------------- | ----------------- |
| 0.000 | 1.000 | 0.000 | 0.600 | 0.000 |
| 0.002 | 1.000 | 0.000 | 0.600 | 0.000 |
| 0.005 | 1.000 | 0.000 | 0.600 | 0.000 |
| 0.010 | 1.000 | 0.000 | 0.600 | 0.000 |
| 0.020 | 1.000 | 0.000 | 0.600 | 0.000 |
| 0.050 | 1.000 | **1.000** | 1.000 | **1.000** |

Interpretation: with a channel holding `L · n = 32` copies, a single flipped copy
already trips the per-copy QBER rule.  At `p = 0.05` the expected number of
flipped copies is `32 · 0.05 = 1.6`, so essentially every *legitimate* transaction
is rejected - the operating point collapses entirely.  The design target stated in
`DetectionConfig` ("false alarms near 1% while `p ≤ 0.01`") is met: below `p = 0.02`
the false-alarm rate is 0 in this fixed-seed run.

## Group-size sweep (distillable amplification)

`g` → Pauli detection / statistical false alarm / mean mismatch rate over
legitimate + channel-attack trials / runtime (50 trials per point):

| g | statistical false alarm | pauli detection | mean E | mean runtime |
| - | ----------------------- | --------------- | ------ | ------------ |
| 1 | 0.000 | 1.000 | 0.2750 | 12.2 ms |
| 2 | 0.000 | 1.000 | 0.2500 | 12.0 ms |
| 3 | 0.000 | 1.000 | 0.2500 | 11.8 ms |
| 4 | 0.000 | 1.000 | 0.2321 | 11.7 ms |

All group sizes detect the channel attack perfectly with zero false alarms.
Increasing `g` measurably lowers the mean mismatch rate (the parity check
collapses whole groups rather than individual copies) and slightly reduces
runtime (fewer measurements).  `g = 1` degenerates to independent per-copy
checks; the fixed protocol default `g = 2` sits in the stable middle of the
sweep.

## Runtime benchmark

Mean wall-clock per scenario over 20 repetitions (`scripts/benchmark.py`):

```
legitimate                       11.25 ms
forgery                          11.05 ms
impersonation                    10.73 ms
replay                           11.03 ms
unauthorized_verification        11.12 ms
channel_manipulation             11.91 ms
OVERALL                          11.18 ms  (120 transactions)
```

## Reproducibility

Everything is seeded from `ExperimentConfig.seed` (`20260101`); every RNG stream
is derived from the seed plus a per-transaction offset.  Rerun with:

```
python scripts/generate_report.py --trials 200 --sweep-trials 50
```