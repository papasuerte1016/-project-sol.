#!/usr/bin/env python3
"""Project Sol host-independent runtime supervisor."""
import json,os,sqlite3,time,urllib.request
from pathlib import Path
STATE_DIR=Path(os.getenv("SOL_STATE_DIR","/data")); DB=Path(os.getenv("SOL_DB",str(STATE_DIR/"sol.db")))
MODEL=os.getenv("SOL_LOCAL_MODEL","qwen2.5:0.5b")
MODEL_BASE=os.getenv("SOL_MODEL_BASE",os.getenv("SOL_MODEL_URL","http://127.0.0.1:11434")).split("/v1/",1)[0].rstrip("/")
RECEIPT=STATE_DIR/"runtime-receipt.json"
def request(path,payload=None,timeout=600):
 data=None if payload is None else json.dumps(payload).encode(); req=urllib.request.Request(MODEL_BASE+path,data=data,headers={"Content-Type":"application/json"})
 with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode())
def state_ready():
 STATE_DIR.mkdir(parents=True,exist_ok=True); c=sqlite3.connect(DB); c.execute("create table if not exists runtime_state(k text primary key,v text)"); c.commit(); c.close(); return str(DB)
def model_ready():
 names={m.get("name","") for m in request("/api/tags",timeout=30).get("models",[])}
 if MODEL not in names: request("/api/pull",{"model":MODEL,"stream":False},timeout=900); names={m.get("name","") for m in request("/api/tags",timeout=30).get("models",[])}
 return MODEL in names
def inference_ready():
 out=request("/api/generate",{"model":MODEL,"prompt":"Reply exactly: SOL READY","stream":False,"options":{"num_ctx":1024,"num_predict":8}},timeout=int(os.getenv("SOL_MODEL_TIMEOUT","600"))); return (out.get("response") or "").strip()
def check():
 r={"ok":False,"time":int(time.time()),"state":None,"model":False,"inference":None}
 try:
  r["state"]=state_ready(); r["model"]=model_ready()
  if not r["model"]:raise RuntimeError("model recovery failed")
  r["inference"]=inference_ready(); r["ok"]=bool(r["inference"])
 except Exception as e:r["error"]=repr(e)
 STATE_DIR.mkdir(parents=True,exist_ok=True); RECEIPT.write_text(json.dumps(r,indent=2)); print(json.dumps(r),flush=True); return r
if __name__=="__main__":
 while True: check(); time.sleep(int(os.getenv("SOL_CHECK_INTERVAL","300")))
