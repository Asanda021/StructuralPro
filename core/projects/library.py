"""Project library services: search, clone, health, export and revision access."""
from __future__ import annotations
from .store import ProjectStore
from .workflow import project_health,copy_project,export_package,import_package
class ProjectLibrary:
    def __init__(self,store:ProjectStore): self.store=store
    def search(self,text=""):
        q=text.casefold().strip()
        rows=self.store.list()
        return [x for x in rows if not q or q in x["id"].casefold() or q in x["name"].casefold()]
    def health(self,project_id):
        p=self.store.get(project_id)
        if p is None: raise KeyError(project_id)
        return project_health(p)
    def clone(self,project_id,new_id):
        p=self.store.get(project_id)
        if p is None: raise KeyError(project_id)
        out=copy_project(p,new_id); self.store.save(new_id,out); return self.store.get(new_id)
    def revisions(self,project_id): return self.store.revisions(project_id)
    def export(self,project_id,path):
        p=self.store.get(project_id)
        if p is None: raise KeyError(project_id)
        return export_package(p,path)
    def import_into_store(self,path,project_id=None):
        p=import_package(path); pid=project_id or p["id"]; p["id"]=pid; self.store.save(pid,p); return p
