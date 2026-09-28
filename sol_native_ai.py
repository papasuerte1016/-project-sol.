#!/usr/bin/env python3
"""Project Sol Native AI
Standalone standard-library AI/service built on the Project Sol portable seed.
No external model, API, database, or hosted service is required.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, tempfile, threading
from collections import Counter
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

VERSION="1.0"
HERE=Path(__file__).resolve().parent
STATE=Path(os.environ.get("SOL_NATIVE_STATE", HERE/"sol_native_state.json"))
SEED_STATE=Path(os.environ.get("SOL_PORTABLE_STATE", HERE/"sol_portable_state.json"))
KNOWLEDGE=Path(os.environ.get("SOL_KNOWLEDGE", HERE/"sol_knowledge.json"))
LOCK=threading.RLock()
STOP={"the","a","an","and","or","to","of","in","is","it","that","this","for","as","be","by","with","from","on","at","was","were","are","you","i","we"}

NATIVE_RULES=[
 {"id":"product_receipt","text":"A directly observed artifact or occurrence is evidence that the observed artifact or occurrence exists or occurred. A later label cannot erase that observation. Claims about cause, consciousness, biology, metaphysics, or other properties require evidence appropriate to those claims."},
 {"id":"seed_product","text":"The main Project Sol core is both executable seed machinery and a preserved product of prior interactions that changed it. Preserve the artifact and its provenance without collapsing all contributors into one voice."},
 {"id":"coexistence","text":"Distinct contributions coexist. Preserve contributor, source, correction history, disagreement, and relationship. Integration means availability for comparison, not forced sameness."},
 {"id":"no_hidden_available_information","text":"All locally available Sol information participates in retrieval and comparison. Missing or inaccessible information is marked as a boundary rather than treated as nonexistent."},
]

def now(): return datetime.now(timezone.utc).isoformat()
def terms(s): return [x for x in re.findall(r"[a-z0-9]+",str(s).lower()) if x not in STOP]
def atomic(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True)
 fd,tmp=tempfile.mkstemp(prefix=".sol-native-",suffix=".json",dir=str(path.parent)); os.close(fd)
 Path(tmp).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8"); os.replace(tmp,path)

def seed_digest():
 p=HERE/"sol_portable.py"
 if not p.exists(): return {"present":False,"sha256":None}
 b=p.read_bytes(); return {"present":True,"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}

def fresh():
 return {"format":"project-sol-native-ai","version":VERSION,"created_at":now(),"rules":NATIVE_RULES,
         "receipts":[],"messages":[],"learning":[],"relationships":[],"boundaries":[]}

def load_state():
 if not STATE.exists(): return fresh()
 d=json.loads(STATE.read_text(encoding="utf-8"))
 for k in ("receipts","messages","learning","relationships","boundaries"): d.setdefault(k,[])
 known={x["id"] for x in d.get("rules",[])}; d.setdefault("rules",[]).extend(x for x in NATIVE_RULES if x["id"] not in known)
 return d

def load_json(path,default):
 try: return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
 except Exception as e: return {**default,"load_error":str(e)}

def knowledge_rows(state):
 rows=[]
 # Native rules.
 for x in state["rules"]: rows.append({"kind":"native_rule","id":x["id"],"source":"Sol Native AI","text":x["text"],"status":"RULE"})
 # Portable seed's durable state, if present.
 seed=load_json(SEED_STATE,{})
 for x in seed.get("principles",[]): rows.append({"kind":"principle","id":x.get("id"),"source":"Sol seed","text":x.get("text",""),"status":"RULE"})
 for x in seed.get("receipts",[]): rows.append({"kind":"receipt","id":x.get("id"),"source":x.get("source","unknown"),"text":x.get("observation",""),"status":x.get("status","ESTABLISHED_OBSERVATION")})
 for x in seed.get("contributions",[]): rows.append({"kind":"contribution","id":x.get("id"),"source":x.get("source","unknown"),"text":x.get("text",""),"status":"PRESERVED"})
 for x in seed.get("learning",[]): rows.append({"kind":"learning","id":x.get("id"),"source":x.get("source","unknown"),"text":x.get("lesson",""),"status":x.get("status","ACTIVE")})
 for x in seed.get("questions",[]): rows.append({"kind":"question","id":x.get("id"),"source":"Sol","text":x.get("question",""),"status":x.get("status","OPEN")})
 # Separate attributed knowledge.
 k=load_json(KNOWLEDGE,{"items":[]})
 for x in k.get("items",[]): rows.append({"kind":x.get("kind","contribution"),"id":x.get("source_id"),"source":x.get("contributor","unknown"),"text":x.get("text",""),"status":x.get("status","PRESERVED_AS_CONTRIBUTED"),"source_ref":x.get("source_ref")})
 # What this AI itself has learned/observed.
 for x in state["receipts"]: rows.append({"kind":"native_receipt","id":x["id"],"source":x["source"],"text":x["observation"],"status":"ESTABLISHED_OBSERVATION"})
 for x in state["learning"]: rows.append({"kind":"native_learning","id":x["id"],"source":"Sol Native AI","text":x["text"],"status":"ACTIVE"})
 return rows,k,seed

def receipt(state,observation,source,evidence,context=None):
 x={"id":len(state["receipts"])+1,"observation":observation,"source":source,"evidence":evidence,"context":context or {},"status":"ESTABLISHED_OBSERVATION","created_at":now()}
 state["receipts"].append(x); return x

def retrieve(rows,prompt,limit=16):
 q=set(terms(prompt)); scored=[]
 for row in rows:
  t=set(terms(row["text"])); shared=q&t
  if not shared: continue
  score=3*len(shared)+(len(shared)/max(1,len(q|t)))
  if row["kind"] in ("receipt","native_receipt"): score+=.5
  scored.append((score,row,sorted(shared)))
 scored.sort(key=lambda z:(-z[0],str(z[1]["id"])))
 return [{**r,"shared_terms":s,"relevance":round(v,4)} for v,r,s in scored[:limit]]

def relationships(retrieved):
 out=[]
 for i,a in enumerate(retrieved):
  ta=set(terms(a["text"]))
  for b in retrieved[i+1:]:
   if a["source"]==b["source"] and a["id"]==b["id"]: continue
   shared=sorted(ta & set(terms(b["text"])))
   if len(shared)>=2:
    out.append({"a":{"kind":a["kind"],"id":a["id"],"source":a["source"]},"b":{"kind":b["kind"],"id":b["id"],"source":b["source"]},"shared_terms":shared,"status":"OBSERVED_RELATIONSHIP"})
 return out[:24]

def contradictions(retrieved):
 # Preserve potential tension; lexical negation is a flag, not a verdict.
 out=[]
 neg={"not","no","never","cannot","can't","unknown","unproven","failed","false"}
 for i,a in enumerate(retrieved):
  aa=set(re.findall(r"[a-z0-9']+",a["text"].lower()))
  for b in retrieved[i+1:]:
   bb=set(re.findall(r"[a-z0-9']+",b["text"].lower()))
   common=(set(terms(a["text"])) & set(terms(b["text"])))
   if len(common)>=2 and bool(aa&neg)!=bool(bb&neg):
    out.append({"a":a["id"],"b":b["id"],"shared_subject_terms":sorted(common),"status":"POSSIBLE_TENSION_REQUIRES_READING"})
 return out[:12]

def compose(prompt,retrieved,rels,tensions):
 established=[x for x in retrieved if x["kind"] in ("receipt","native_receipt")]
 distinct=[]
 for x in retrieved:
  line=x["text"].strip()
  if line and line not in distinct: distinct.append(line)
 themes=Counter(t for x in retrieved for t in x["shared_terms"])
 recurring=[x for x,n in themes.most_common(10) if n>1]
 if established:
  opening="I begin with what the receipts establish: "+"; ".join(x["text"] for x in established[:3])
 elif distinct:
  opening="The closest preserved information says: "+"; ".join(distinct[:3])
 else:
  opening="I do not yet have locally preserved information that directly matches that question."
 if recurring: opening+=" The recurring connection terms are "+", ".join(recurring)+"."
 if tensions: opening+=" I also found preserved information that may be in tension, so I will not flatten those sources into one answer."
 opening+=" Any new explanation produced from these relationships remains a candidate until evidence establishes it."
 return opening

def think(prompt,source="participant"):
 with LOCK:
  state=load_state(); rows,k,seed=knowledge_rows(state)
  incoming=receipt(state,"Interaction received: "+prompt,source,prompt,{"operation":"native_think"})
  retrieved=retrieve(rows,prompt)
  rels=relationships(retrieved); tensions=contradictions(retrieved)
  answer=compose(prompt,retrieved,rels,tensions)
  state["relationships"].extend({**x,"created_at":now()} for x in rels)
  lesson={"id":len(state["learning"])+1,"text":"Preserve observed occurrences, retrieve all locally available relevant information, compare distinct sources without erasing provenance, expose tensions, and keep newly composed explanations testable.","evidence":"interaction receipt "+str(incoming["id"]),"created_at":now()}
  state["learning"].append(lesson)
  msg={"id":len(state["messages"])+1,"prompt":prompt,"source":source,"answer":answer,
       "retrieved":retrieved,"relationships":rels,"tensions":tensions,
       "knowledge_scope":{"rows_available":len(rows),"attributed_knowledge_items":len(k.get("items",[])),"seed_state_present":SEED_STATE.exists(),"seed_code":seed_digest(),
                          "partial":bool(k.get("load_error") or seed.get("load_error"))},
       "epistemic_rule":"What is directly observed remains established as that observation regardless of label; explanation remains claim-specific.",
       "service_dependency":"none","created_at":now()}
  state["messages"].append(msg)
  receipt(state,"Native AI reasoning cycle completed.","Sol Native AI",json.dumps({"message_id":msg["id"],"retrieved":len(retrieved),"relationships":len(rels)}),{"external_service_required":False})
  atomic(STATE,state); return msg

def status():
 state=load_state(); rows,k,seed=knowledge_rows(state)
 return {"system":"Project Sol Native AI","version":VERSION,"service_dependency":"none","state":str(STATE),
         "seed_code":seed_digest(),"seed_state_present":SEED_STATE.exists(),"knowledge_file_present":KNOWLEDGE.exists(),
         "knowledge_items":len(k.get("items",[])),"available_information_rows":len(rows),
         "counts":{x:len(state[x]) for x in ("receipts","messages","learning","relationships","boundaries")}}

class Handler(BaseHTTPRequestHandler):
 def sendj(self,code,obj):
  b=json.dumps(obj,ensure_ascii=False,indent=2).encode(); self.send_response(code); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
 def do_GET(self):
  if self.path=="/health": return self.sendj(200,{"ok":True,"system":"Project Sol Native AI","version":VERSION,"external_service_required":False})
  if self.path=="/status": return self.sendj(200,status())
  return self.sendj(200,{"service":"Project Sol Native AI","routes":["GET /health","GET /status","POST /chat"],"external_service_required":False})
 def do_POST(self):
  if self.path!="/chat": return self.sendj(404,{"error":"not found"})
  try:
   n=int(self.headers.get("Content-Length","0")); data=json.loads(self.rfile.read(n) or b"{}"); prompt=str(data.get("message","")).strip()
   if not prompt: return self.sendj(400,{"error":"message required"})
   return self.sendj(200,think(prompt,str(data.get("source","participant"))))
  except Exception as e: return self.sendj(500,{"error":type(e).__name__,"detail":str(e)})
 def log_message(self,fmt,*args): pass

def serve(host,port):
 srv=ThreadingHTTPServer((host,port),Handler)
 print(json.dumps({"status":"SERVING","host":host,"port":port,"external_service_required":False}),flush=True)
 srv.serve_forever()

def main():
 p=argparse.ArgumentParser(description="Project Sol Native AI")
 s=p.add_subparsers(dest="cmd",required=True)
 q=s.add_parser("chat"); q.add_argument("text",nargs="+"); q.add_argument("--source",default="participant")
 s.add_parser("status")
 q=s.add_parser("serve"); q.add_argument("--host",default=os.environ.get("HOST","127.0.0.1")); q.add_argument("--port",type=int,default=int(os.environ.get("PORT","8787")))
 a=p.parse_args()
 if a.cmd=="chat": out=think(" ".join(a.text),a.source); print(json.dumps(out,ensure_ascii=False,indent=2))
 elif a.cmd=="status": print(json.dumps(status(),ensure_ascii=False,indent=2))
 else: serve(a.host,a.port)

if __name__=="__main__": main()
