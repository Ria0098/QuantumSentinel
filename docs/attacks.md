# Threat model and the five attack simulations

The problem statement's threat categories map onto five concrete attack classes
plus the benign baseline.  Every attack produces a declarative `AttackOutcome`
and is executed by the shared `QuantumChannel` and `QDSSession` machinery.

| Key | Class | What it does | Measurement-visible? |
| --- | ----- | ------------ | --------------------- |
| `legitimate` | `BenignExchange` | No adversarial action (false-alarm baseline) | n/a |
| `forgery` | `SignatureForgery` | Guesses the key bit-by-bit and forges qubits; wrong guesses are eigenstates of the wrong Pauli operator | yes |
| `impersonation` | `Impersonation` | Presents a well-formed signature bound to the attacker's *own* key while claiming to be the sender | yes |
| `replay` | `ReplayAttack` | Re-submits a previously accepted transaction (same message, key, nonce) | **no** |
| `unauthorized_verification` | `UnauthorizedVerification` | Genuine, unmodified transaction submitted by an entity outside the authorised set | **no** |
| `channel_manipulation` | `ChannelManipulation` | Injects Pauli errors, forges classical teleportation bits, drops qubits and disturbs the witness | yes |

## UC-1 Signature forgery

The adversary does **not** know the shared key, so it guesses.  A guessed key
matches the real one on roughly half the positions.  Where the guess is wrong the
forged qubit is an eigenstate of the wrong Pauli operator, and the verifier's
own-basis measurement of it returns a random `±1` with probability 1.  Detected by
both the protocol (per-copy mismatch) and the Pauli layer (eigenvalue agreement
collapses).

## UC-2 Sender impersonation

The impersonator has a *legitimate* key — its own — and uses it to build an
internally consistent signature, relabelling the transaction as coming from the
real sender.  The signature is consistent with the wrong key, so mismatch
concentrates exactly on the positions where the attacker's key differs from the
verifier's.  This is deliberately different from forgery: forging is random noise,
impersonation is a *valid* signature bound to the wrong secret.

## UC-3 Replay attack

The adversary replays the quantum transcript of a previously accepted
transaction.  Every Pauli expectation and measurement outcome is reproduced
exactly.  **Replay is invisible to any measurement-based detector by
construction**; it is caught by the classical freshness (nonce) cache in
`ReplayCache`, which is part of the statistical layer's rule set.  The evaluation
reports the Pauli layer's failure to see this as an honest false negative.

## UC-4 Unauthorised verification

A genuine, unmodified transaction is submitted by a requesting entity outside the
authorised set `{alice, victor}`.  The quantum state is untouched and all
measurements agree.  Like replay, this is invisible to the Pauli layer and is
caught by the authorisation rule in the statistical layer.

## UC-5 Quantum channel manipulation

The adversary attacks the transport rather than the protocol logic, using four
primitive disturbances that model genuinely different attacker capabilities:

* **Pauli decoherence** (`pauli_decoherence`): random non-identity Pauli error on
  copies.  Flips the target eigenvalue with probability 1 for an eigenstate.
* **Classical tampering** (`classical_tamper`): forges the two teleportation
  bits, so the receiver applies the wrong correction.  The residual Pauli is
  random and flips the eigenvalue only half the time — genuinely weaker.
* **Photon loss** (`photon_loss`): drops copies; detected by *counting*.
* **Witness disturbance** (`witness_disturbance`): degrades the retained Bell
  pairs, attacking the entanglement witness itself.

The default `ChannelManipulation` uses 100% Pauli errors, 50% classical
tampering, 0% loss, and 50% witness disturbance.

## Small-print honesty

* The channel simulation and the detection layers share the same vocabulary
  (`Disturbance` / statistical signals).  Physical noise and adversarial activity
  are deliberately indistinguishable, so the false-alarm benchmark is honest.
* `expected_quantum_visible` is a *ground-truth* property recorded on each
  `AttackOutcome`; the evaluation compares the measured detection rate against it
  rather than assuming perfect detection.