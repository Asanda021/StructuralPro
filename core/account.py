"""Provider-neutral local account and device identity; no mandatory cloud service."""
from __future__ import annotations
import hashlib,secrets
from dataclasses import dataclass,asdict
@dataclass(frozen=True)
class Account:
    account_id:str; display_name:str; created_at:str
@dataclass(frozen=True)
class DeviceIdentity:
    device_id:str; platform:str
def make_account(display_name,account_id=None,created_at=""): return Account(account_id or "acct_"+secrets.token_hex(8),display_name,created_at)
def device_identity(platform="desktop",seed=None):
    raw=(seed or secrets.token_hex(16)).encode()
    return DeviceIdentity("dev_"+hashlib.sha256(raw).hexdigest()[:16],platform)
