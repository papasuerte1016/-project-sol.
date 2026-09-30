import tempfile
from pathlib import Path
from sol_repo_runtime import SolRepoRuntime
with tempfile.TemporaryDirectory() as d:
 r=SolRepoRuntime(Path(d))
 a=r.record('create',{'a.txt':'one'},['test'])
 b=r.record('change',{'a.txt':'two','b.txt':'new'},['test'])
 assert b['parents']==[a['commit']]
 assert (Path(d)/'Sol_Repository'/'refs'/'main').read_text()==b['commit']
 assert r.repo.compare(a['commit'],b['commit'])=={'added':['b.txt'],'removed':[],'changed':['a.txt'],'same':[]}
 print('SOL_AUTO_REPOSITORY_INTEGRATION=PASS')
