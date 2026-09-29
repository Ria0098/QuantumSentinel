# Detection design

Both layers consume exactly the same `DetectionInput` and are compared fairly.
**Neither layer is AI or ML**: all signals are arithmetic, closed-form
statistics of the measurement data or classical protocol rules, compared against
fixed constants from `DetectionConfig`.

## Method 1 - statistical detection (`StatisticalDetector`)

Classical statistics of the verification run plus the two classical protocol
rules whose failure no measurement can expose.

| Signal | Meaning | Trip rule |
| ------ | ------- | --------- |
| `mismatch_rate` | `E = N_mismatch / N` over all check families | `> 0.05` |
| `qber` | per-copy quantum bit error rate over single-qubit family | `> 0.02` |
| `per_basis_qber_X` / `per_basis_qber_Z` | same rate per key-dictated basis | `> 0.05` |
| `coverage_shortfall` | fraction of expected copies never returned | `> 0` |
| `replay` | nonce already accepted | violated |
| `authorisation` | requesting entity not in authorised set | violated |

The last two are intentionally classical: replay and unauthorised verification
leave the quantum data perfect, so only a protocol-context rule can see them.

## Method 2 - Pauli-measurement detection (`PauliMeasurementDetector`)

Restricted to **quantum measurement data and the verifier's record of the
message**.  It never reads nonces, identities or authorisation state.

| Signal | Meaning | Trip rule |
| ------ | ------- | --------- |
| `eigenvalue_agreement_X/Z` | mean Pauli expectation over copies targeted at `+1` | `< 0.90` |
| `basis_distribution_distance_X/Z` | TV distance between observed and expected `+1` fractions | `> 0.20` |
| `parity_agreement_X/Z` | fraction of cat-state groups whose parity matched their intended parity | `< 0.90` |
| `entanglement_witness` | fraction of Bell pairs whose two-body correlators match the ideal | `< 0.90` |

Because replay and unauthorised verification produce measurement data identical
to the legitimate baseline, the Pauli layer *correctly reports them as
legitimate*.  The results document that as the honest limit of measurement-based
detection.

## Composite verdict

`DetectionEngine` runs both layers and reports:

* per-detector verdicts,
* agreement between them,
* the full per-basis measurement summary,
* the set of signals that tripped.

A transaction is considered a threat if **either** layer trips; the report
always shows both verdicts so the reader can see how much the Pauli layer
contributes on top of the classical rules.

## Why the two layers disagree (and why that is a feature)

The design intentionally surfaces where quantum measurements *can* and *cannot*
establish an attack:

* forgery, impersonation, channel manipulation ⇨ both layers trip;
* replay, unauthorised verification ⇨ statistical-only (quantum-invisible).

The scenario table and the metrics in `docs/results.md` and `results/` report all
of this quantitatively, including the Pauli layer's measured false negatives.