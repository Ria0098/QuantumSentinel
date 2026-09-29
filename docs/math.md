# Mathematical model

## Notation

* `L` - number of message bits (`message_length`, default 8).
* `n` - teleportation copies per message bit (`copies_per_bit`, default 4).
* `m`, `k` - message and shared key, both `L`-bit strings.
* `v_i = m_i ⊕ k_i` - the *signed value* at position `i`.
* `σ_i ∈ {X, Z}` - key-dictated measurement basis: `k_i = 0 → Z`, `k_i = 1 → X`.
* `|b⟩_σ` - eigenstate of Pauli `σ` with eigenvalue `(-1)^b`.
* `λ = (-1)^{sign_bit}` - Bell resource sign (default `+1`).

## Signature qubits

The sender prepares, for every position `i`, the qubit `|v_i⟩_{σ_i}`.  The verifier
knows `m` and `k`, hence `v_i`, hence both the basis and the target eigenvalue
`(-1)^{v_i}` of every transmitted copy.

## Distribution by teleportation

Each of the `L·n` signature qubits is teleported through a *fresh* Bell pair

```
|Φ(λ)⟩_σ = ( |0,0⟩_σ + λ |1,1⟩_σ ) / √2
```

using the three-qubit circuit `CNOT(input → sender_half)`, `H(input)`, two
computational-basis measurements, and the Pauli correction `Z^m1 X^m2` applied by
the receiver.  The two bits `(m1, m2)` travel over the *classical* control
channel.

**Correlator identity.** For `|Φ(λ)⟩_σ`,

```
⟨σ ⊗ σ⟩ = +1
⟨τ ⊗ τ⟩ = λ      (τ = the other basis axis)
⟨Z ⊗ X⟩ = ⟨X ⊗ Z⟩ = 0
```

This is the pattern the *entanglement witness* checks against.

## Distillable amplification (parity checks)

Copies at one message position are grouped into consecutive groups of `g`
(`parity_group_size`, default 2), `g = 2` giving the GHZ/cat-state picture.  The
products of each position's copies are *not* measured individually; instead the
product observable

```
Π = σ ⊗ σ ⊗ … ⊗ σ   (g copies)
```

is measured.  Because the group state factorises,

```
⟨Π⟩ = ∏_j ⟨σ_j⟩,
                P(parity = +1) = (1 + ⟨Π⟩)/2.
```

A single error in the group anticommutes with exactly one factor and therefore
flips the parity **with probability 1**.  This is the amplification: one parity
check detects any *odd* number of errors inside its group regardless of `g`, while
`s` independent per-copy checks miss a lone error with probability
`(1 - q)^s`.

`g = 1` degenerates the parity check to a single-qubit check; the sweeps in the
results report the measured trade-off between group size, mismatch rate and
runtime.

## Error model

`pauli_decoherence` applies a uniformly random non-identity Pauli
`P ∈ {X, Y, Z}` to a fraction of copies.  `P` flips the eigenvalue of a `σ`
eigenstate exactly when `P` anticommutes with `σ` — probability `2/3`.  The
*classical* tamper attack instead forges the correction bits, leaving a uniformly
random residual Pauli that flips the eigenvalue with probability `1/2` — which is
why one Pauli flip per copy has probability `1/2` of producing a mismatched
signature eigenvalue.

`photon_loss` drops qubits outright; a per-qubit measurement cannot notice a
missing qubit, so detection of loss is by *counting* copies (coverage check).

## Verification statistics

Every check compares an observed eigenvalue (or parity) to the target printed by
the verifier's own record:

```
E = N_mismatch / N_all     mismatch rate over single + parity + witness + coverage
QBER = N_mismatch_single / N_single
```

The statistical detector trips if any of its scalar statistics exceeds the fixed
threshold in `DetectionConfig` (defaults: `E > 0.05`, `QBER > 0.02`, per-basis
`QBER > 0.05`, coverage shortfall `> 0`, freshness/authorisation violated).

## Pauli-measurement observables

For each basis the Pauli layer reports:

* **Eigenvalue agreement** - mean `⟨σ⟩` over copies targeted at the `+1`
  eigenstate (`+1` ideal).
* **Basis distribution distance** - total-variation distance between the observed
  and *expected* fraction of `+1` outcomes (`0` ideal).  The expected fraction is
  derived from the signed message, not assumed uniform.
* **Parity agreement** - fraction of cat-state groups whose measured parity
  matched the group's intended parity (`1` ideal).

The **entanglement witness** is the fraction of retained Bell pairs whose four
two-body correlators `ZZ, XX, ZX, XZ` still match the ideal pattern above.

## Detection limits (measured, not assumed)

Replay and unauthorised verification leave the measurement transcript
bit-identical to a legitimate run.  *No* measurement-based detector can see them;
the statistical layer alone adds the classical freshness/authorisation rules.  The
evaluation reports this honestly as the Pauli layer's measured false negatives.