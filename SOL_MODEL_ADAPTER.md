# Sol Model Adapter v0.1

This connects Sol Compute Tokens to **actual model inference** on a model endpoint that voluntarily accepts Sol's protocol on the Sol side.

Flow: verify ledger → check units → call model → successful answer → spend units → chained receipt.

Environment:
- `SOL_MODEL_URL` — OpenAI-compatible chat-completions endpoint (default local Ollama-compatible URL).
- `SOL_LOCAL_MODEL` — model name exposed by that endpoint.
- `SOL_MODEL_API_KEY` — optional credential for a self-controlled/private endpoint.
- `SOL_TOKEN_DB`, `SOL_TOKEN_SECRET` — token ledger configuration.

Example after a compatible local/self-hosted model is running:
`python sol_compute_token.py issue 10 "compute allocation" sol`
`python sol_model_adapter.py sol "What did Sol learn?"`

Important: Sol units authorize/account for Sol-controlled compute. They are not OpenAI credits and do not bypass any provider's billing or access controls.
