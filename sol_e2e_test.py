#!/usr/bin/env python3
"""Project Sol service startup probe: model test + durable process."""
import json
import time
import sol_compute_token as token
import sol_model_adapter as model

ACCOUNT="sol-test"
PROMPT="Reply exactly: SOL MODEL ONLINE"

issue=token.mint(ACCOUNT,5,"end-to-end model test allocation")
try:
    result=model.execute(ACCOUNT,PROMPT)
    model_ok=True
except Exception as exc:
    result={"ok":False,"error":str(exc)}
    model_ok=False
verification=token.verify()
out={
  "ok": model_ok,
  "supply_policy": token.policy(),
  "issue_receipt": issue,
  "inference": result,
  "ledger_valid": verification["valid"],
  "ledger_verification": verification,
}
print(json.dumps(out,indent=2),flush=True)

# Keep the Railway service alive even if the model edge is temporarily down.
# The failed probe remains visible as a receipt instead of killing the service.
while True:
    time.sleep(3600)
