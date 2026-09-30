from pathlib import Path
import hashlib,json,time
from sol_repo_runtime import SolRepoRuntime
class SolConnectionHub:
 def __init__(self,root): self.root=Path(root); self.runtime=SolRepoRuntime(self.root); self.adapters={}
 def register(self,name,adapter): self.adapters[name]=adapter
 def record(self,kind,payload,source='Sol',evidence=None):
  data=json.dumps({'kind':kind,'source':source,'payload':payload},sort_keys=True)
  receipt=self.runtime.record(kind,{f'events/{source}/{time.time_ns()}.json':data},evidence or [],source)
  return receipt
 def publish(self,receipt):
  results={}
  for name,a in self.adapters.items():
   try: results[name]={'ok':True,'result':a(receipt)}
   except Exception as e: results[name]={'ok':False,'error':type(e).__name__+': '+str(e)}
  return results
 def ingest(self,source,payload,evidence=None): return self.record('ingest',payload,source,evidence)
 def change(self,source,path,content,evidence=None):
  return self.runtime.record('change',{path:content},evidence or [],source)
 def ask_reply(self,prompt,reply,evidence=None):
  return self.runtime.record('ask_reply',{'conversation/prompt.txt':prompt,'conversation/reply.txt':reply},evidence or [],'Sol')
