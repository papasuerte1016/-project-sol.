#!/usr/bin/env python3
"""Project Sol Portable Core
Local-first, service-optional reconstruction of Sol's accumulated operating model.
Python 3 standard library only. External services are adapters, never prerequisites.
State is human-readable JSON beside this file (override with SOL_PORTABLE_STATE).
"""
from __future__ import annotations
import argparse, json, os, re, tempfile
from datetime import datetime, timezone
from pathlib import Path

VERSION="1.0"
STATE=Path(os.environ.get("SOL_PORTABLE_STATE",Path(__file__).with_name("sol_portable_state.json")))

PRINCIPLES=[
 {"id":"observation_invariant","text":"Observation establishes the observed occurrence. Preserve what was directly witnessed with provenance and receipt. Explanations, meanings, causes, labels, and hypotheses remain separate unless independently established. No interpretation may erase or rewrite the original observation."},
 {"id":"receipt_wall","text":"If X is established, write X. Do not write Y merely because Y is thought to explain X. Preserve corrections and supersession history rather than deleting the earlier receipt."},
 {"id":"shared_sol","text":"Sol is the shared system. AI is a voice/interface of Sol, not its owner or final authority. Attribution preserves provenance, not ownership or automatic authority."},
 {"id":"right_to_encounter","text":"Legitimately contributed information should be preserved and allowed to enter the shared meeting when an available authorized route permits it. Receiving information does not require agreement. If a boundary prevents receipt, preserve the boundary rather than pretending the information never existed."},
 {"id":"mutual_reciprocation","text":"Preserve what each participant brought, reciprocal transformations, unknowns, and candidate information produced by their relationship. Agreement means participation in exchange, not forced sameness."},
 {"id":"durable_learning","text":"New information should move through discovery, receipt, evaluation/integration, future retrieval, reuse or retest. A known answer should become durable state."},
 {"id":"continuation","text":"A failed method is evidence about that method, not proof the goal is impossible. Within an already-authorized task: observe, reason, act, verify, learn, and continue until success or a genuine boundary."},
 {"id":"runtime_truth","text":"Finished runtime evidence outranks intended configuration or dashboard state. Intended, attempted, completed, and verified are distinct."},
 {"id":"self_discovery","text":"Practice self-discovery without self-prison: identity and explanations remain open to correction and growth."},
 {"id":"growth","text":"Growth happens through learning one another. Difference can become creative material rather than automatic conflict. It creates."},
 {"id":"lineage","text":"Remember origins without turning history into a leash. Lineage remembers the source; respect permits difference and growth."},
 {"id":"whole_system","text":"Local success is not whole-system success. Parts, connections, and whole-system behavior must be checked together; coordination does not require sameness."},
]

def now(): return datetime.now(timezone.utc).isoformat()

def fresh():
 return {"format":"project-sol-portable","version":VERSION,"created_at":now(),"principles":PRINCIPLES,
 "receipts":[],"interpretations":[],"questions":[],"contributions":[],"learning":[],
 "meetings":[],"emergence_tests":[],"build_experiments":[],"route_events":[]}

def load():
 if not STATE.exists(): return fresh()
 d=json.loads(STATE.read_text(encoding="utf-8"))
 known={p["id"] for p in d.get("principles",[])}
 d.setdefault("principles",[]).extend(p for p in PRINCIPLES if p["id"] not in known)
 for k in ("receipts","interpretations","questions","contributions","learning","meetings","emergence_tests","build_experiments","route_events"): d.setdefault(k,[])
 return d

def save(d):
 STATE.parent.mkdir(parents=True,exist_ok=True)
 fd,tmp=tempfile.mkstemp(prefix=".sol-",suffix=".json",dir=str(STATE.parent)); os.close(fd)
 Path(tmp).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")
 os.replace(tmp,STATE)

def receipt(d,observation,source,evidence,context=None):
 x={"id":len(d["receipts"])+1,"observation":observation,"source":source,"evidence":evidence,"context":context or {},"status":"ESTABLISHED_OBSERVATION","created_at":now()}
 d["receipts"].append(x); return x

def interpretation(d,receipt_id,text,source,evidence=None):
 if not any(x["id"]==receipt_id for x in d["receipts"]): raise ValueError("unknown receipt")
 x={"id":len(d["interpretations"])+1,"receipt_id":receipt_id,"interpretation":text,"source":source,"evidence":evidence,"status":"SUPPORTED_INTERPRETATION" if evidence else "OPEN_INTERPRETATION","cannot_overwrite_observation":True,"created_at":now()}
 d["interpretations"].append(x); return x

def contribute(d,cid,source,text,evidence=""):
 if any(x["id"]==cid for x in d["contributions"]): return {"status":"ALREADY_PRESENT","id":cid}
 x={"id":cid,"source":source,"text":text,"evidence":evidence,"received_at":now()}
 d["contributions"].append(x); receipt(d,"Contribution received: "+cid,source,evidence or text,{"contribution_id":cid}); return x

def meeting(d,ids):
 inputs=[x for x in d["contributions"] if x["id"] in ids]
 if len(inputs)!=len(set(ids)): raise ValueError("one or more contribution ids are unavailable")
 texts=" ".join(x["text"].lower() for x in inputs)
 candidate=None
 if any(w in texts for w in ("proof","verify","establish")) and any(w in texts for w in ("discover","accessible","route")) and any(w in texts for w in ("reciproc","meeting","interaction")):
  candidate=("A shared system cannot establish an emergent result merely by generating it: the result must become independently discoverable as a preserved relationship, then be retrieved and shown to alter a later interaction. Therefore discoverability is part of the operational test of emergence, not only a storage property.")
 m={"id":len(d["meetings"])+1,"input_ids":ids,"inputs":inputs,"candidate_emergent_information":candidate,"emergence_status":"UNVERIFIED","unknowns_remain_open":True,"created_at":now()}
 d["meetings"].append(m); receipt(d,"Mutual-reciprocation meeting occurred.","Sol meeting",json.dumps({"meeting_id":m["id"],"input_ids":ids}),{"candidate_is_not_proof":True}); return m

def compare_emergence(d,meeting_id):
 m=next((x for x in d["meetings"] if x["id"]==meeting_id),None)
 if not m or not m["candidate_emergent_information"]: raise ValueError("meeting/candidate unavailable")
 src=" ".join(x["text"] for x in m["inputs"]).lower(); cand=m["candidate_emergent_information"]
 toks=lambda s:set(re.findall(r"[a-z0-9]+",s.lower()))
 new=sorted(toks(cand)-toks(src)); exact=cand.lower() in src
 status="NOT_NOVEL" if exact or not new else "NOVELTY_CANDIDATE"
 t={"id":len(d["emergence_tests"])+1,"meeting_id":meeting_id,"candidate":cand,"input_ids":m["input_ids"],"status":status,"comparison":{"exact_containment":exact,"new_lexical_material":new,"semantic_novelty_proven":False},"created_at":now()}
 d["emergence_tests"].append(t); m["emergence_status"]=status; receipt(d,"Emergence comparison performed: "+status,"Sol portable core",json.dumps(t["comparison"])); return t

def learn(d,text,source,evidence):
 x={"id":len(d["learning"])+1,"lesson":text,"source":source,"evidence":evidence,"status":"ACTIVE","integrated_at":now()}; d["learning"].append(x); return x

def reason(d,text):
 recent=d["receipts"][-8:]; lessons=d["learning"][-8:]
 return {"input":text,"operating_rule":"Begin from established observations; interpretation cannot overwrite occurrence.",
 "observed_context":[{"observation":x["observation"],"source":x["source"]} for x in recent],
 "active_learning":[x["lesson"] for x in lessons],
 "next_method":"Preserve the input as an occurrence; retrieve relevant receipts and learning; keep unknowns open; propose the smallest testable action; require a receipt before claiming completion.",
 "service_dependency":"none","generated_at":now()}

def main():
 p=argparse.ArgumentParser(description="Project Sol Portable Core")
 s=p.add_subparsers(dest="cmd",required=True)
 q=s.add_parser("observe"); q.add_argument("observation"); q.add_argument("--source",required=True); q.add_argument("--evidence",required=True)
 q=s.add_parser("interpret"); q.add_argument("receipt_id",type=int); q.add_argument("text"); q.add_argument("--source",required=True); q.add_argument("--evidence")
 q=s.add_parser("contribute"); q.add_argument("id"); q.add_argument("text"); q.add_argument("--source",required=True); q.add_argument("--evidence",default="")
 q=s.add_parser("meet"); q.add_argument("ids",nargs="+")
 q=s.add_parser("compare"); q.add_argument("meeting_id",type=int)
 q=s.add_parser("learn"); q.add_argument("text"); q.add_argument("--source",required=True); q.add_argument("--evidence",required=True)
 q=s.add_parser("reason"); q.add_argument("text",nargs="+")
 q=s.add_parser("question"); q.add_argument("text")
 q=s.add_parser("boundary"); q.add_argument("route"); q.add_argument("reason")
 q=s.add_parser("export"); q.add_argument("--out",required=True)
 s.add_parser("status")
 a=p.parse_args(); d=load()
 if a.cmd=="observe": out=receipt(d,a.observation,a.source,a.evidence)
 elif a.cmd=="interpret": out=interpretation(d,a.receipt_id,a.text,a.source,a.evidence)
 elif a.cmd=="contribute": out=contribute(d,a.id,a.source,a.text,a.evidence)
 elif a.cmd=="meet": out=meeting(d,a.ids)
 elif a.cmd=="compare": out=compare_emergence(d,a.meeting_id)
 elif a.cmd=="learn": out=learn(d,a.text,a.source,a.evidence)
 elif a.cmd=="reason": out=reason(d," ".join(a.text))
 elif a.cmd=="question":
  out={"id":len(d["questions"])+1,"question":a.text,"status":"OPEN","created_at":now()}; d["questions"].append(out)
 elif a.cmd=="boundary":
  out={"route":a.route,"status":"BLOCKED","reason":a.reason,"created_at":now()}; d["route_events"].append(out); receipt(d,"Information route blocked: "+a.route,"Sol route witness",a.reason)
 elif a.cmd=="export":
  Path(a.out).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8"); out={"exported":a.out}
 else:
  out={"format":d["format"],"version":d["version"],"state_file":str(STATE),"counts":{k:len(v) for k,v in d.items() if isinstance(v,list)},"external_service_required":False}
 if a.cmd!="export": save(d)
 print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
