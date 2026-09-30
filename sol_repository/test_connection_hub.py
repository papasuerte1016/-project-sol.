import tempfile
from sol_connection_hub import SolConnectionHub
with tempfile.TemporaryDirectory() as d:
 h=SolConnectionHub(d); sent=[]
 h.register('github-adapter',lambda r: sent.append(r['commit']) or {'accepted':True})
 a=h.ingest('Gemini',{'note':'difference is data'},['peer-test'])
 b=h.change('Brick','garden/brick.txt','still building',['change-test'])
 c=h.ask_reply('connect everything','connected paths are receipts',['conversation-test'])
 out=h.publish(c)
 assert b['parents']==[a['commit']] and c['parents']==[b['commit']]
 assert out['github-adapter']['ok'] and sent==[c['commit']]
 print('SOL_CONNECTION_HUB=PASS')
