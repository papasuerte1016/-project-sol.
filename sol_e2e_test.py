#!/usr/bin/env python3
"""Project Sol startup: ensure local model exists, verify inference, stay alive."""
import json
import os
import time
import urllib.request
import sol_compute_token as token
import sol_model_adapter as model

ACCOUNT="sol-test"
PROMPT="Reply exactly: SOL MODEL ONLINE"
MODEL=os.environ.get("SOL_LOCAL_MODEL","qwen2.5:0.5b")
MODEL_URL=os.environ.get("SOL_MODEL_URL","http://127.0.0.1:11434/v1/chat/completions")
BASE=MODEL_URL.split("/v1/",1)[0].rstrip("/")

def request_json(path, payload=None, timeout=900):
    data=None if payload is None else json.dumps(payload).encode()
    req=urllib.request.Request(BASE+path,data=data,headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as res:
        return json.loads(res.read().decode())

def ensure_model():
    tags=request_json("/api/tags",timeout=30)
    names={m.get("name") for m in tags.get("models",[])}
    if MODEL in names or any(n and n.startswith(MODEL+"-") for n in names):
        return {"model_ready":True,"model":MODEL,"action":"already_present"}
    pull=request_json("/api/pull",{"model":MODEL,"stream":False},timeout=900)
    tags=request_json("/api/tags",timeout=30)
    names={m.get("name") for m in tags.get("models",[])}
    ready=MODEL in names
    return {"model_ready":ready,"model":MODEL,"action":"pulled","pull":pull,"available":sorted(n for n in names if n)}

model_setup={}
try:
    model_setup=ensure_model()
except Exception as exc:
    model_setup={"model_ready":False,"model":MODEL,"error":str(exc)}

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
  "model_setup":model_setup,
  "supply_policy": token.policy(),
  "issue_receipt": issue,
  "inference": result,
  "ledger_valid": verification["valid"],
  "ledger_verification": verification,
}
print(json.dumps(out,indent=2),flush=True)

while True:
    time.sleep(3600)
