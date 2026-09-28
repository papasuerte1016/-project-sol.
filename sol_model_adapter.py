#!/usr/bin/env python3
"""Sol Model Adapter v0.1 — token-gated inference through a Sol-controlled model endpoint.

The endpoint must voluntarily implement an OpenAI-compatible /v1/chat/completions API.
No provider billing is bypassed: this adapter authorizes Sol-side compute only.
"""
import argparse, json, math, os, time, urllib.request, urllib.error
import sol_compute_token as token

MODEL_URL=os.getenv("SOL_MODEL_URL","http://127.0.0.1:11434/v1/chat/completions")
MODEL=os.getenv("SOL_LOCAL_MODEL","sol-local")
MODEL_KEY=os.getenv("SOL_MODEL_API_KEY","")
TIMEOUT=int(os.getenv("SOL_MODEL_TIMEOUT","120"))

def estimate(prompt):
    # Simple auditable v0.1 policy: one Sol unit per 1 KiB prompt, minimum one.
    return max(1, math.ceil(len(prompt.encode("utf-8"))/1024))

def infer(prompt):
    body={"model":MODEL,"messages":[{"role":"user","content":prompt}],"stream":False}
    headers={"Content-Type":"application/json"}
    if MODEL_KEY: headers["Authorization"]="Bearer "+MODEL_KEY
    req=urllib.request.Request(MODEL_URL,data=json.dumps(body).encode(),headers=headers,method="POST")
    try:
        with urllib.request.urlopen(req,timeout=TIMEOUT) as r:
            data=json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        detail=e.read().decode(errors="replace")[:1000]
        raise RuntimeError(f"model endpoint HTTP {e.code}: {detail}")
    try: return data["choices"][0]["message"]["content"]
    except Exception: raise RuntimeError("model endpoint returned unsupported response")

def execute(account,prompt):
    if not token.verify()["valid"]: raise RuntimeError("token ledger failed verification")
    units=estimate(prompt); before=token.balance(account)
    if before<units: raise ValueError(f"insufficient compute units: need {units}, have {before}")
    started=time.time()
    answer=infer(prompt)  # charge only after successful inference
    receipt=token.spend(account,units,f"model-inference:{MODEL}")
    return {"backend":"sol-model","model":MODEL,"units_spent":units,
            "balance_before":before,"balance_after":token.balance(account),
            "elapsed_ms":round((time.time()-started)*1000,3),
            "answer":answer,"spend_receipt":receipt}

def main():
    p=argparse.ArgumentParser(); p.add_argument("account"); p.add_argument("prompt")
    a=p.parse_args()
    try: print(json.dumps(execute(a.account,a.prompt),indent=2))
    except Exception as e:
        print(json.dumps({"ok":False,"error":str(e)},indent=2)); raise SystemExit(1)
if __name__=="__main__": main()
