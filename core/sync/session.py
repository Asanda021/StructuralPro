"""Optional authenticated sync session contract; core remains offline without it."""
from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class SyncSession:
    account_id:str; device_id:str; access_token:str|None=None
    @property
    def authenticated(self): return bool(self.access_token)
