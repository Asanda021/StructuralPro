"""Deterministic in-memory sync provider used for offline/E2E tests and demos."""
from __future__ import annotations
from copy import deepcopy
class MemorySyncProvider:
    def __init__(self): self.records={}
    def push(self,records):
        for r in records:
            self.records[(str(r["project_id"]),int(r["version"]))]=deepcopy(r)
        return {"pushed":len(records)}
    def pull(self,project_id):
        rows=[deepcopy(v) for (pid,_),v in self.records.items() if pid==str(project_id)]
        rows.sort(key=lambda x:int(x["version"]))
        return rows
