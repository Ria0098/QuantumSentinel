# Scenario report

Produced with seed `20260101`.

## Scenario: Legitimate transaction (`legitimate`)

- Adversarial action: No disturbance applied. This is the false-alarm baseline.
- Ground truth: benign | quantum-visible in measurement data: False
- Protocol decision: ACCEPT
- Runtime: 10.93 ms

### Verification

- Signature valid: True
- Freshness: True
- Authorisation: True
- Reject reason: none
- Mismatch rate E = 0.0000 (0/64)

### Method 1: statistical

signal               value  rule  threshold  tripped
------------------  ------  ----  ---------  -------
mismatch_rate       0.0000  >        0.0500  no
qber                0.0000  >        0.0200  no
per_basis_qber_X    0.0000  >        0.0500  no
per_basis_qber_Z    0.0000  >        0.0500  no
coverage_shortfall  0.0000  >        0.0000  no
replay              0.0000  >        0.0000  no
authorisation       0.0000  >        0.0000  no

### Method 2: pauli_measurement

signal                          value  rule  threshold  tripped
-----------------------------  ------  ----  ---------  -------
eigenvalue_agreement_X         1.0000  <        0.9000  no
basis_distribution_distance_X  0.0000  >        0.2000  no
parity_agreement_X             1.0000  <        0.9000  no
eigenvalue_agreement_Z         1.0000  <        0.9000  no
basis_distribution_distance_Z  0.0000  >        0.2000  no
parity_agreement_Z             1.0000  <        0.9000  no
entanglement_witness           1.0000  <        0.9000  no

## Scenario: Signature forgery (`forgery`)

- Adversarial action: Guessed 4/8 key bits correctly. At the remaining 4 positions the forged qubit is an eigenstate of the wrong Pauli operator, so the verifier's own-basis measurement returns a random +-1 with probability 1.
- Ground truth: ATTACK | quantum-visible in measurement data: True
- Protocol decision: REJECT
- Runtime: 10.49 ms

### Verification

- Signature valid: False
- Freshness: True
- Authorisation: True
- Reject reason: per-copy measurement mismatch; distillation parity mismatch
- Mismatch rate E = 0.2188 (14/64)

### Method 1: statistical

signal               value  rule  threshold  tripped
------------------  ------  ----  ---------  -------
mismatch_rate       0.2188  >        0.0500  yes
qber                0.2812  >        0.0200  yes
per_basis_qber_X    0.6667  >        0.0500  yes
per_basis_qber_Z    0.4000  >        0.0500  yes
coverage_shortfall  0.0000  >        0.0000  no
replay              0.0000  >        0.0000  no
authorisation       0.0000  >        0.0000  no

### Method 2: pauli_measurement

signal                          value  rule  threshold  tripped
-----------------------------  ------  ----  ---------  -------
eigenvalue_agreement_X         1.0000  <        0.9000  no
basis_distribution_distance_X  0.0000  >        0.2000  no
parity_agreement_X             0.6667  <        0.9000  yes
eigenvalue_agreement_Z         0.3333  <        0.9000  yes
basis_distribution_distance_Z  0.0000  >        0.2000  no
parity_agreement_Z             0.7000  <        0.9000  yes
entanglement_witness           1.0000  <        0.9000  no

## Scenario: Sender impersonation (`impersonation`)

- Adversarial action: 'mallory' submitted a signature bound to their own key while claiming to be 'alice'. The key differs on 6 of 8 positions, so those qubits are eigenstates of the wrong Pauli operator.
- Ground truth: ATTACK | quantum-visible in measurement data: True
- Protocol decision: REJECT
- Runtime: 10.79 ms

### Verification

- Signature valid: False
- Freshness: True
- Authorisation: True
- Reject reason: per-copy measurement mismatch; distillation parity mismatch
- Mismatch rate E = 0.2344 (15/64)

### Method 1: statistical

signal               value  rule  threshold  tripped
------------------  ------  ----  ---------  -------
mismatch_rate       0.2344  >        0.0500  yes
qber                0.3125  >        0.0200  yes
per_basis_qber_X    0.5000  >        0.0500  yes
per_basis_qber_Z    1.0000  >        0.0500  yes
coverage_shortfall  0.0000  >        0.0000  no
replay              0.0000  >        0.0000  no
authorisation       0.0000  >        0.0000  no

### Method 2: pauli_measurement

signal                          value  rule  threshold  tripped
-----------------------------  ------  ----  ---------  -------
eigenvalue_agreement_X         1.0000  <        0.9000  no
basis_distribution_distance_X  0.0833  >        0.2000  no
parity_agreement_X             0.8750  <        0.9000  yes
eigenvalue_agreement_Z         0.0000  <        0.9000  yes
basis_distribution_distance_Z  0.0000  >        0.2000  no
parity_agreement_Z             0.5000  <        0.9000  yes
entanglement_witness           1.0000  <        0.9000  no

## Scenario: Replay attack (`replay`)

- Adversarial action: Replayed transaction 1ab940301548ef89 (nonce 102614821015). The quantum transcript is identical to the original, so only the classical freshness check can see it.
- Ground truth: ATTACK | quantum-visible in measurement data: False
- Protocol decision: REJECT
- Runtime: 10.66 ms

### Verification

- Signature valid: True
- Freshness: False
- Authorisation: True
- Reject reason: nonce replay
- Mismatch rate E = 0.0000 (0/64)

### Method 1: statistical

signal               value  rule  threshold  tripped
------------------  ------  ----  ---------  -------
mismatch_rate       0.0000  >        0.0500  no
qber                0.0000  >        0.0200  no
per_basis_qber_X    0.0000  >        0.0500  no
per_basis_qber_Z    0.0000  >        0.0500  no
coverage_shortfall  0.0000  >        0.0000  no
replay              1.0000  >        0.0000  yes
authorisation       0.0000  >        0.0000  no

### Method 2: pauli_measurement

signal                          value  rule  threshold  tripped
-----------------------------  ------  ----  ---------  -------
eigenvalue_agreement_X         1.0000  <        0.9000  no
basis_distribution_distance_X  0.0000  >        0.2000  no
parity_agreement_X             1.0000  <        0.9000  no
eigenvalue_agreement_Z         1.0000  <        0.9000  no
basis_distribution_distance_Z  0.0000  >        0.2000  no
parity_agreement_Z             1.0000  <        0.9000  no
entanglement_witness           1.0000  <        0.9000  no

## Scenario: Unauthorized verification attempt (`unauthorized_verification`)

- Adversarial action: 'eve' requested verification but is not in the authorised set ['alice', 'victor']. The quantum state is untouched.
- Ground truth: ATTACK | quantum-visible in measurement data: False
- Protocol decision: REJECT
- Runtime: 10.76 ms

### Verification

- Signature valid: True
- Freshness: True
- Authorisation: False
- Reject reason: unauthorised verifying entity
- Mismatch rate E = 0.0000 (0/64)

### Method 1: statistical

signal               value  rule  threshold  tripped
------------------  ------  ----  ---------  -------
mismatch_rate       0.0000  >        0.0500  no
qber                0.0000  >        0.0200  no
per_basis_qber_X    0.0000  >        0.0500  no
per_basis_qber_Z    0.0000  >        0.0500  no
coverage_shortfall  0.0000  >        0.0000  no
replay              0.0000  >        0.0000  no
authorisation       1.0000  >        0.0000  yes

### Method 2: pauli_measurement

signal                          value  rule  threshold  tripped
-----------------------------  ------  ----  ---------  -------
eigenvalue_agreement_X         1.0000  <        0.9000  no
basis_distribution_distance_X  0.0000  >        0.2000  no
parity_agreement_X             1.0000  <        0.9000  no
eigenvalue_agreement_Z         1.0000  <        0.9000  no
basis_distribution_distance_Z  0.0000  >        0.2000  no
parity_agreement_Z             1.0000  <        0.9000  no
entanglement_witness           1.0000  <        0.9000  no

## Scenario: Quantum channel manipulation (`channel_manipulation`)

- Adversarial action: Pauli errors on 100% of copies, forged classical teleportation bits on 50%, 0% of copies dropped, and 50% of witness pairs disturbed.
- Ground truth: ATTACK | quantum-visible in measurement data: True
- Protocol decision: REJECT
- Runtime: 11.71 ms

### Verification

- Signature valid: False
- Freshness: True
- Authorisation: True
- Reject reason: entanglement witness mismatch; per-copy measurement mismatch; distillation parity mismatch
- Mismatch rate E = 0.4531 (29/64)

### Method 1: statistical

signal               value  rule  threshold  tripped
------------------  ------  ----  ---------  -------
mismatch_rate       0.4531  >        0.0500  yes
qber                0.5938  >        0.0200  yes
per_basis_qber_X    0.8125  >        0.0500  yes
per_basis_qber_Z    0.3750  >        0.0500  yes
coverage_shortfall  0.0000  >        0.0000  no
replay              0.0000  >        0.0000  no
authorisation       0.0000  >        0.0000  no

### Method 2: pauli_measurement

signal                           value  rule  threshold  tripped
-----------------------------  -------  ----  ---------  -------
eigenvalue_agreement_X         -0.7500  <        0.9000  yes
basis_distribution_distance_X   0.0625  >        0.2000  no
parity_agreement_X              0.6250  <        0.9000  yes
eigenvalue_agreement_Z          0.1667  <        0.9000  yes
basis_distribution_distance_Z   0.2500  >        0.2000  yes
parity_agreement_Z              0.5000  <        0.9000  yes
entanglement_witness            0.6250  <        0.9000  yes
