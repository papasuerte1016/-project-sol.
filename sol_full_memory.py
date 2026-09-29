import base64,gzip,json,re
from pathlib import Path
ROOT=Path(__file__).parent
def load():
    s="".join((ROOT/"knowledge_chunks"/f"chunk{i:02}.b64").read_text().strip() for i in range(6))
    raw=gzip.decompress(base64.b64decode(s))
    return json.loads(raw)
def retrieve(query,k=24):
    rows=load(); q=set(re.findall(r"[a-z0-9']+",query.lower()))
    scored=[]
    for r in rows:
        v=r.get("value",""); w=set(re.findall(r"[a-z0-9']+",v.lower()))
        score=len(q&w)
        if score: scored.append((score,r))
    return [r for _,r in sorted(scored,key=lambda x:(x[0],x[1].get("id",0)),reverse=True)[:k]]
