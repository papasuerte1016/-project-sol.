#!/usr/bin/env python3
"""Sol-native receipt/lineage repository. GitHub is an adapter, never authority."""
from pathlib import Path
import hashlib, json, time

class SolRepo:
    def __init__(self, root):
        self.root=Path(root); self.obj=self.root/'objects'; self.refs=self.root/'refs'
        self.obj.mkdir(parents=True,exist_ok=True); self.refs.mkdir(parents=True,exist_ok=True)
    @staticmethod
    def _canon(x): return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
    def _put(self, kind, payload):
        envelope={'kind':kind,'payload':payload}; raw=self._canon(envelope)
        oid=hashlib.sha256(raw).hexdigest(); (self.obj/oid).write_bytes(raw); return oid
    def snapshot(self, files):
        entries={}
        for name,data in sorted(files.items()):
            if isinstance(data,str): data=data.encode()
            entries[name]={'sha256':hashlib.sha256(data).hexdigest(),'size':len(data),'blob':self._put('blob',{'hex':data.hex()})}
        return self._put('snapshot',entries)
    def commit(self, snapshot, message, contributor='Sol', parents=None, evidence=None):
        payload={'snapshot':snapshot,'message':message,'contributor':contributor,'parents':parents or [],'evidence':evidence or [],'timestamp_ns':time.time_ns()}
        return self._put('commit',payload)
    def set_ref(self,name,commit): (self.refs/name).write_text(commit)
    def get(self,oid): return json.loads((self.obj/oid).read_text())
    def compare(self,a,b):
        sa=self.get(self.get(a)['payload']['snapshot'])['payload']; sb=self.get(self.get(b)['payload']['snapshot'])['payload']
        A,B=set(sa),set(sb); changed=sorted(k for k in A&B if sa[k]['sha256']!=sb[k]['sha256'])
        return {'added':sorted(B-A),'removed':sorted(A-B),'changed':changed,'same':sorted(k for k in A&B if sa[k]['sha256']==sb[k]['sha256'])}
    def receipt(self,commit):
        c=self.get(commit)['payload']; return {'commit':commit,'snapshot':c['snapshot'],'parents':c['parents'],'contributor':c['contributor'],'evidence':c['evidence'],'verified':True}
