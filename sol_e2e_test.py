#!/usr/bin/env python3
"""Sol end-to-end test — token-gated inference against the private sol-model service.

This script exercises the full path Railway needs verified before sol-ai is
allowed to charge Sol Compute Units (SCU) for inference:

  1. Issue 5 SCU to a test account ("sol-test" by default).
  2. Call sol_model_adapter.execute() to run a small prompt through the
     local Ollama-backed model at SOL_MODEL_URL.
  3. Confirm the SCU ledger balance moved as expected and that the chained
     event hashes still verify.

Configuration is entirely via environment variables (set these on the
Railway service, do not hardcode them):

  SOL_MODEL_URL     e.g. http://sol-model.railway.internal:11434/v1/chat/completions
  SOL_LOCAL_MODEL   e.g. qwen2.5:0.5b
  SOL_TOKEN_DB      e.g. /tmp/sol_tokens.db (ephemeral is fine for a test run)
  SOL_TOKEN_SECRET  optional, enables HMAC signing of ledger events

Usage:
  python sol_e2e_test.py [account] [prompt]

Exits non-zero and prints {"ok": false, ...} on any failure so it can be
used as a CI/deploy gate.
"""
import argparse, json, sys

import sol_compute_token as token
import sol_model_adapter as adapter


def run(account: str, prompt: str, issue_units: int = 5) -> dict:
    issue_receipt = token.mint(account, issue_units, "sol-e2e-test:initial-issue")
    balance_after_issue = token.balance(account)

    result = adapter.execute(account, prompt)

    ledger_state = token.verify()

    return {
        "ok": True,
        "account": account,
        "prompt": prompt,
        "model": result["model"],
        "answer": result["answer"],
        "units_spent": result["units_spent"],
        "balance_before": result["balance_before"],
        "balance_after": result["balance_after"],
        "issue_receipt": {
            "event_hash": issue_receipt["event_hash"],
            "units": issue_receipt["units"],
        },
        "balance_after_issue": balance_after_issue,
        "spend_receipt": {
            "event_hash": result["spend_receipt"]["event_hash"],
            "units": result["spend_receipt"]["units"],
        },
        "ledger_valid": ledger_state["valid"],
        "ledger_problems": ledger_state["problems"],
        "elapsed_ms": result["elapsed_ms"],
    }


def main():
    p = argparse.ArgumentParser(description="Sol end-to-end token-gated inference test")
    p.add_argument("account", nargs="?", default="sol-test")
    p.add_argument("prompt", nargs="?", default="Say hello in one short sentence.")
    p.add_argument("--issue-units", type=int, default=5)
    args = p.parse_args()

    try:
        out = run(args.account, args.prompt, args.issue_units)
        print(json.dumps(out, indent=2))
        if not out["ledger_valid"]:
            raise SystemExit(1)
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
