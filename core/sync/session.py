"""Optional authenticated sync session contract and token persistence boundary."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
@dataclass(frozen=True)
class SyncSession:
    account_id:str; device_id:str; access_token:str|None=None
    @property
    def authenticated(self): return bool(self.access_token)
    def require_auth(self):
        if not self.authenticated: raise PermissionError("sync authentication required")
        return self
class SyncAuthenticator:
    """Provider-neutral authentication boundary; the backend is injected by the product build."""
    def __init__(self,authenticate:Callable[[str,str],str]): self._authenticate=authenticate
    def login(self,account_id,secret): return SyncSession(account_id,"",self._authenticate(account_id,secret))
