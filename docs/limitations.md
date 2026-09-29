# Limitations and honest scope

This prototype is a **pedagogical, classical-NumPy simulation** of a
quantum-inspired detection pipeline.  It is not a production security product
and its numbers should be read as mean-behaviour demonstrations, not as
physical guarantees.

## Conceptual limits

1. **Classical simulation, not real quantum hardware.**  All states are dense
   amplitude vectors and all outcomes are sampled from exact Born-rule
   probabilities.  Real devices introduce continuous gate errors, finite
   visibility, measurement misclassification and decoherence profiles that a
   bit-flip Pauli model does not capture.

2. **`reduced_single_qubit` uses the dominant eigenvector.**  For a single-qubit
   *product* state (every state this protocol measures) the marginal is pure and
   the eigenvector reproduces the exact state and all Pauli expectations.  It is
   deliberately **not** a general mixed-state partial trace; the Bell-pair
   marginal in the entanglement witness is measured with the exact two-body
   correlator, not with this helper.

3. **Protocol scale.**  `L = 8` and `n = 4` keep the simulation fast; the
   statistical power of the thresholds (e.g. `QBER > 0.02`) and the noise
   "knee" at `p ≈ 0.02–0.05` are consequences of that small register, not of the
   protocol design at large `L`.  Scaling `L` and `n` requires re-deriving
   operating points, not just re-running.

4. **No AI/ML.**  The two detectors are fixed threshold rules.  When the problem
   statement asks for a "quantum-inspired model", this prototype answers with
   closed-form Pauli statistics plus classical protocol rules.  It deliberately
   uses **no neural network, no statistical classifier**; nothing is trained or
   fitted to the attack data.

## Detection limits the prototype measures

5. **Replay and unauthorised verification are quantum-invisible.**
   Measurement statistics cannot distinguish a replayed transcript from a fresh
   one.  Catching them requires the classical freshness (nonce cache) and
   authorisation rules, which are part of the statistical layer.  The evaluation
   therefore reports the Pauli layer at 60% detection by design.

6. **Threshold calibration is hand-set.**  The thresholds in `DetectionConfig`
   are analytic choices targeting low false alarms for `p ≤ 0.01`.  A real
   deployment should calibrate them against the actual hardware error budget.

## Threat-model limits

7. The simulator assumes an attack on the channel, the signature, or the
   verification *context*.  It does **not** model a malicious verifier, a
   corrupted shared-key infrastructure, a denial of service at the transport
   layer, or side channels (timing, EM, power) on the simulated hardware.

8. `pauli_decoherence` is a depolarising Pauli channel with uniform weights.
   Real amplitude/phase damping, correlated errors and coherent (unitary) errors
   are not modelled, although the same verification statistics would partially
   respond to them.

## Engineering scope

9. Performance: the statevector engine is exact but unoptimised; the per-copy
   teleportation allocates intermediate arrays.  Runtime is ~11 ms per
   transaction on this machine, fine for a prototype and a SIH demo, not for a
   high-throughput service.

10. Imports/dependencies: the package requires only NumPy and runs on
    CPython ≥ 3.10 (developed against 3.14.7/NumPy 2.5.x).

A full threat-and-limitations table mapping to the PRD is in
`docs/prd-traceability.md`.