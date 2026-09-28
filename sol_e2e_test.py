#!/usr/bin/env python3
"""One-shot Project Sol SCU -> model -> receipt integration proof."""
import json
import sol_compute_token as token
import sol_model_adapter as model

ACCOUNT="sol-test"
PROMPT="Reply exactly: SOL MODEL ONLINE"

issue=token.mint(ACCOUNT,5,"end-to-end model test allocation")
result=model.execute(ACCOUNT,PROMPT)
verification=token.verify()
out={
  "ok": model_ok,
  "supply_policy": token.policy(),
  "issue_receipt": issue,
  "inference": result,
  "ledger_valid": verification["valid"],
  "ledger_verification": verification,
}
print(json.dumps(out,indent=2),flush=True)\n# Railway service mode: preserve the process after the startup probe so a\n# temporarily unavailable model edge does not crash the Sol AI service.\nwhile True:\n    time.sleep(3600)
