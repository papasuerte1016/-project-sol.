"""Live-adapter capability probes for Sol.
Adapters are supplied by the host. A probe reports only what the host actually exposes.
"""
class SolLiveAdapterProbes:
 def __init__(self, registry, adapters):
  self.registry=registry; self.adapters=adapters
 def install(self):
  for name,adapter in sorted(self.adapters.items()):
   self.registry.register(name,self._probe(name,adapter),condition='current host runtime')
  return list(sorted(self.adapters))
 def _probe(self,name,adapter):
  def run():
   if adapter is None: return {'ok':False,'evidence':['adapter missing'],'error':'not exposed by host'}
   probe=getattr(adapter,'probe',None)
   if callable(probe):
    r=probe()
    if isinstance(r,dict): return r
    return {'ok':bool(r),'evidence':['adapter probe returned '+repr(r)]}
   return {'ok':True,'evidence':['adapter object exposed by host','no active network/write test performed']}
  return run

def install_standard_host_adapters(registry, **adapters):
 return SolLiveAdapterProbes(registry,adapters).install()
