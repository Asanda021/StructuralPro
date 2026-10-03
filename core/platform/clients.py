"""Provider-neutral Windows/Android/Telegram client contract."""
from dataclasses import dataclass
from typing import Any
SUPPORTED_PLATFORMS=("windows","android","telegram")
@dataclass(frozen=True)
class ClientRequest:
    request_id:str; platform:str; action:str; project_id:str; payload:dict[str,Any]
    def __post_init__(self):
        if self.platform not in SUPPORTED_PLATFORMS: raise ValueError("unsupported client platform")
        if not self.request_id.strip() or not self.action.strip() or not self.project_id.strip(): raise ValueError("request identity is required")
@dataclass(frozen=True)
class ClientResponse:
    request_id:str; ok:bool; data:dict[str,Any]; error:str=""
    def __post_init__(self):
        if self.ok and self.error: raise ValueError("successful response cannot contain an error")
        if not self.ok and not self.error: raise ValueError("failed response requires an error")
def capability_manifest():
    return {"windows":{"offline":True,"sync":True,"reports":True,"takeoff":True},"android":{"offline":True,"sync":True,"reports":True,"takeoff":True},"telegram":{"offline":False,"sync":True,"reports":True,"takeoff":True}}
