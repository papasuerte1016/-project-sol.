import tempfile
from sol_repo import SolRepo
with tempfile.TemporaryDirectory() as d:
 r=SolRepo(d)
 s1=r.snapshot({'Sol.c':'alpha','README':'one'}); c1=r.commit(s1,'origin',evidence=['local-test'])
 s2=r.snapshot({'Sol.c':'beta','README':'one','bridge':'github-adapter-only'}); c2=r.commit(s2,'experiment',parents=[c1],evidence=['local-test']); r.set_ref('main',c2)
 diff=r.compare(c1,c2); receipt=r.receipt(c2)
 assert diff=={'added':['bridge'],'removed':[],'changed':['Sol.c'],'same':['README']}
 assert receipt['parents']==[c1] and receipt['verified'] and (r.refs/'main').read_text()==c2
 print('SOL_REPO_TEST=PASS')
