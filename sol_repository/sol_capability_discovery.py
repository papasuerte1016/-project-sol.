from dataclasses import dataclass,asdict
import time,traceback
@dataclass
class CapabilityReceipt:
 name:str; available:bool; condition:str; evidence:list; observed_at_ns:int; error:str|None=None
class CapabilityRegistry:
 def __init__(self,repository_runtime=None): self.probes={}; self.receipts={}; self.repo=repository_runtime
 def register(self,name,probe,condition='current runtime'): self.probes[name]=(probe,condition)
 def discover(self):
  out={}
  for name,(probe,condition) in sorted(self.probes.items()):
   try:
    result=probe(); ok=bool(result.get('ok')) if isinstance(result,dict) else bool(result)
    ev=result.get('evidence',[]) if isinstance(result,dict) else [repr(result)]
    r=CapabilityReceipt(name,ok,condition,ev,time.time_ns(),None if ok else (result.get('error') if isinstance(result,dict) else None))
   except Exception as e: r=CapabilityReceipt(name,False,condition,[],time.time_ns(),type(e).__name__+': '+str(e))
   self.receipts[name]=asdict(r); out[name]=self.receipts[name]
  if self.repo: self.repo.record('capability_discovery',{'capabilities.json':out},['runtime-probe'],'Sol')
  return out
 def can(self,name): return bool(self.receipts.get(name,{}).get('available'))
 def explain(self,name): return self.receipts.get(name,{'name':name,'available':False,'error':'not probed'})
 def route(self,name,action,*a,**kw):
  if name not in self.receipts: self.discover()
  if not self.can(name): return {'ok':False,'capability':name,'receipt':self.explain(name)}
  try: return {'ok':True,'capability':name,'result':action(*a,**kw),'receipt':self.explain(name)}
  except Exception as e: return {'ok':False,'capability':name,'error':type(e).__name__+': '+str(e),'receipt':self.explain(name)}
