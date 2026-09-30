from sol_capability_discovery import CapabilityRegistry
from sol_live_adapter_probes import install_standard_host_adapters
class GitHub:
 def probe(self): return {'ok':True,'evidence':['authenticated connector probe']}
class Build:
 def probe(self): return {'ok':False,'evidence':['service not connected'],'error':'authorization required'}
r=CapabilityRegistry()
names=install_standard_host_adapters(r,github=GitHub(),codemagic=Build(),iphone=None,grok=None,gemini=None)
d=r.discover()
assert names==['codemagic','gemini','github','grok','iphone']
assert d['github']['available'] is True
assert d['codemagic']['available'] is False and d['iphone']['available'] is False
print('SOL_LIVE_ADAPTER_DISCOVERY=PASS')
