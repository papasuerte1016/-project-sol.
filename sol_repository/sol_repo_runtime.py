from pathlib import Path
import json
from sol_repo import SolRepo
class SolRepoRuntime:
    def __init__(self,root):
        self.root=Path(root); self.repo=SolRepo(self.root/'Sol_Repository'); self.ref='main'
    def _parent(self):
        p=self.repo.refs/self.ref
        return p.read_text().strip() if p.exists() else None
    def record(self,event,files,evidence=None,contributor='Sol'):
        normalized={k:(v if isinstance(v,(bytes,str)) else json.dumps(v,sort_keys=True)) for k,v in files.items()}
        snap=self.repo.snapshot(normalized); parent=self._parent()
        commit=self.repo.commit(snap,event,contributor=contributor,parents=[parent] if parent else [],evidence=evidence or [])
        self.repo.set_ref(self.ref,commit); return self.repo.receipt(commit)
