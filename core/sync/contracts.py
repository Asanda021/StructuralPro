"""Provider-neutral sync contracts."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from typing import Any
@dataclass(frozen=True)
class SyncRecord:
    record_id:str; project_id:str; version:int; updated_at:str; payload:dict[str,Any]
    def to_dict(self): return asdict(self)
@dataclass(frozen=True)
class SyncResult:
    pushed:int; pulled:int; conflicts:int; errors:list[str]
class SyncProvider:
    def push(self,records): raise NotImplementedError
    def pull(self,project_id): raise NotImplementedError
