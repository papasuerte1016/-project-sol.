#!/usr/bin/env python3
"""Sol Compute Units v0.2 — unbounded-supply internal compute-access ledger, not money."""
import argparse, hashlib, hmac, json, os, sqlite3, time, uuid

DB=os.getenv("SOL_TOKEN_DB","sol_tokens.db")
SECRET=os.getenv("SOL_TOKEN_SECRET")
SUPPLY_POLICY="UNBOUNDED"

def conn():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
    c.executescript("""CREATE TABLE IF NOT EXISTS token_events(
id TEXT PRIMARY KEY, ts INTEGER NOT NULL, kind TEXT NOT NULL,
src TEXT, dst TEXT, units INTEGER NOT NULL CHECK(units>0),
purpose TEXT NOT NULL, prev_hash TEXT, event_hash TEXT NOT NULL UNIQUE,
signature TEXT);
CREATE INDEX IF NOT EXISTS ix_token_src ON token_events(src);
CREATE INDEX IF NOT EXISTS ix_token_dst ON token_events(dst);""")
    return c

def canonical(x): return json.dumps(x,sort_keys=True,separators=(",",":"))
def sign(s): return hmac.new(SECRET.encode(),s.encode(),hashlib.sha256).hexdigest() if SECRET else None

def append(kind,src,dst,units,purpose):
    if units<=0: raise ValueError("units must be positive")
    c=conn(); last=c.execute("SELECT event_hash FROM token_events ORDER BY rowid DESC LIMIT 1").fetchone()
    prev=last["event_hash"] if last else "GENESIS"
    event={"id":str(uuid.uuid4()),"ts":int(time.time()),"kind":kind,"src":src,"dst":dst,
           "units":units,"purpose":purpose,"prev_hash":prev}
    digest=hashlib.sha256(canonical(event).encode()).hexdigest()
    sig=sign(digest)
    c.execute("INSERT INTO token_events VALUES(?,?,?,?,?,?,?,?,?,?)",
      (event["id"],event["ts"],kind,src,dst,units,purpose,prev,digest,sig)); c.commit()
    return {**event,"event_hash":digest,"signature":sig}

def balance(who):
    c=conn()
    incoming=c.execute("SELECT COALESCE(SUM(units),0) n FROM token_events WHERE dst=?",(who,)).fetchone()["n"]
    outgoing=c.execute("SELECT COALESCE(SUM(units),0) n FROM token_events WHERE src=?",(who,)).fetchone()["n"]
    return incoming-outgoing

def mint(dst,units,purpose):
    # Deliberately no protocol supply cap: SCU supply is unbounded.
    return append("ISSUE",None,dst,units,purpose)

def transfer(src,dst,units,purpose):
    if src==dst: raise ValueError("source and destination must differ")
    if balance(src)<units: raise ValueError("insufficient compute units")
    return append("TRANSFER",src,dst,units,purpose)

def spend(src,units,purpose):
    if balance(src)<units: raise ValueError("insufficient compute units")
    return append("SPEND",src,"SOL_COMPUTE_POOL",units,purpose)

def verify():
    c=conn(); prev="GENESIS"; problems=[]
    for r in c.execute("SELECT * FROM token_events ORDER BY rowid"):
        event={k:r[k] for k in ("id","ts","kind","src","dst","units","purpose","prev_hash")}
        digest=hashlib.sha256(canonical(event).encode()).hexdigest()
        if r["prev_hash"]!=prev: problems.append([r["id"],"broken chain"])
        if digest!=r["event_hash"]: problems.append([r["id"],"hash mismatch"])
        if SECRET and r["signature"]!=sign(r["event_hash"]): problems.append([r["id"],"signature mismatch"])
        prev=r["event_hash"]
    return {"valid":not problems,"problems":problems,"supply_policy":SUPPLY_POLICY}

def policy():
    return {
      "name":"Sol Compute Units",
      "symbol":"SCU",
      "supply_policy":SUPPLY_POLICY,
      "maximum_supply":None,
      "artificial_scarcity":False,
      "information_ownership":False,
      "purpose":"access, coordination, compute accounting, and receipts",
      "note":"Unbounded SCU issuance does not imply unbounded physical compute."
    }

def main():
    p=argparse.ArgumentParser(description="Sol Compute Units: unbounded-supply internal compute access/accounting, not currency.")
    s=p.add_subparsers(dest="cmd",required=True)
    for name in ("issue","transfer","spend"):
        q=s.add_parser(name); q.add_argument("units",type=int); q.add_argument("purpose")
        if name=="issue": q.add_argument("dst")
        elif name=="transfer": q.add_argument("src"); q.add_argument("dst")
        else: q.add_argument("src")
    q=s.add_parser("balance"); q.add_argument("who")
    s.add_parser("verify"); s.add_parser("policy")
    a=p.parse_args()
    if a.cmd=="issue": out=mint(a.dst,a.units,a.purpose)
    elif a.cmd=="transfer": out=transfer(a.src,a.dst,a.units,a.purpose)
    elif a.cmd=="spend": out=spend(a.src,a.units,a.purpose)
    elif a.cmd=="balance": out={"account":a.who,"compute_units":balance(a.who),"supply_policy":SUPPLY_POLICY}
    elif a.cmd=="policy": out=policy()
    else: out=verify()
    print(json.dumps(out,indent=2))

if __name__=="__main__": main()
