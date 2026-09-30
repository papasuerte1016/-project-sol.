from sol_capability_discovery import CapabilityRegistry
r=CapabilityRegistry()
r.register('repository',lambda:{'ok':True,'evidence':['SolRepo importable']})
r.register('peer_transport',lambda:{'ok':False,'evidence':['no live peer adapter in isolated test'],'error':'adapter unavailable'})
r.register('new_unknown_capability',lambda:{'ok':True,'evidence':['discovered without static capability list']})
d=r.discover()
assert r.can('repository') and not r.can('peer_transport') and r.can('new_unknown_capability')
assert r.route('repository',lambda:'used')['ok']
assert not r.route('peer_transport',lambda:'should not run')['ok']
print('SOL_CAPABILITY_DISCOVERY=PASS')
