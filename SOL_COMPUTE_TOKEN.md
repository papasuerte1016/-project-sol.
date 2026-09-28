# Sol Compute Token v0.1

An internal, auditable **compute-credit protocol** for Project Sol. These units are **not money, cryptocurrency, securities, or OpenAI credits** and cannot bypass a provider's billing system.

Principles:
- Units represent permission/accounting for compute in infrastructure that voluntarily recognizes this protocol.
- Shared information is never owned by token holders.
- Tokens grant no ownership, rank, governance authority, or claim over Project Sol.
- Every issue, transfer, and spend is an append-only receipt.
- Events form a SHA-256 hash chain; set `SOL_TOKEN_SECRET` to add HMAC verification.
- Attribution/history are receipts, not property claims.

Commands:
`python sol_compute_token.py issue 100 "initial test allocation" sol-test`
`python sol_compute_token.py balance sol-test`
`python sol_compute_token.py spend 5 "local inference test" sol-test`
`python sol_compute_token.py verify`

Next integration target: make a Sol-controlled model/compute adapter check and spend compute units before running a job.
