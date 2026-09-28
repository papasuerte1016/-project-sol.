# Sol Compute Units (SCU) v0.2

An internal, auditable **compute-access and accounting protocol** for Project Sol. SCU are **not money, cryptocurrency, securities, OpenAI credits, or Railway credits** and cannot bypass a provider's billing or access controls.

## Supply rule: unbounded

Project Sol places **no maximum supply** on SCU. Legitimate issuance may continue without a protocol-level cap. SCU therefore do not derive purpose from artificial scarcity.

**Unbounded token supply does not mean infinite physical compute.** CPU time, memory, storage, network capacity, electricity, and externally purchased infrastructure remain finite. SCU coordinate and receipt access to whatever compute is actually available.

## Sol principles

- SCU exist for access, coordination, compute accounting, and verifiable receipts—not wealth, rank, ownership, or power.
- Shared information is never owned by token holders.
- Holding or receiving SCU grants no ownership, governance authority, status, or claim over Project Sol.
- Information is not made scarce in order to create token value.
- Every issue, transfer, and spend is an append-only receipt.
- Events form a SHA-256 hash chain; set `SOL_TOKEN_SECRET` to add HMAC verification.
- Attribution/history are receipts, not property claims.
- Compute backends remain responsible for real resource limits, scheduling, and capacity.

## Commands

`python sol_compute_token.py policy`

`python sol_compute_token.py issue 100 "test allocation" sol-test`

`python sol_compute_token.py balance sol-test`

`python sol_compute_token.py spend 5 "local inference test" sol-test`

`python sol_compute_token.py verify`

There is intentionally no maximum-supply command or scarcity mechanism.

## Security work still required

Unbounded legitimate issuance is separate from unauthorized ledger modification. A production version should make balance-check + spend atomic and add issuer authorization/public-key verification. Those protections defend receipts and resource coordination; they must not turn SCU into a scarce asset or ownership system.
