"""Project revision manager with version snapshots and deterministic comparisons."""
from __future__ import annotations
from dataclasses import dataclass
from core.revisions.compare import compare_rows, summary

@dataclass(frozen=True)
class Revision:
    version:int
    label:str
    rows:list[dict]

class RevisionManager:
    def __init__(self): self._revisions:list[Revision]=[]

    def add(self, rows, label="")->Revision:
        rev=Revision(len(self._revisions)+1,label or f"نسخه {len(self._revisions)+1}",[dict(x) for x in rows])
        self._revisions.append(rev); return rev

    def list(self): return list(self._revisions)

    def compare(self, old_version:int, new_version:int):
        old=self._revisions[old_version-1].rows; new=self._revisions[new_version-1].rows
        changes=compare_rows(old,new)
        return {"changes":changes,"summary":summary(changes)}

    def latest(self): return self._revisions[-1] if self._revisions else None
