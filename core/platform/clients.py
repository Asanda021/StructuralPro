"""Shared provider-neutral platform contracts; preserves the legacy ProductClient API."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable

@dataclass
class ClientSession:
    platform: str
    project_id: str | None = None
    offline: bool = True

class ProductClient:
    SUPPORTED={"windows","android","telegram"}
    def __init__(self, platform: str, project_service: Callable[...,Any] | None=None):
        platform=str(platform).lower()
        if platform not in self.SUPPORTED: raise ValueError("unsupported platform")
        self.session=ClientSession(platform); self.project_service=project_service
    def open_project(self, project_id: str):
        self.session.project_id=str(project_id)
        if self.project_service: return self.project_service(project_id)
        return {"id":str(project_id),"platform":self.session.platform}
    def state(self)->dict[str,Any]:
        return {"platform":self.session.platform,"project_id":self.session.project_id,"offline":self.session.offline}

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
    return {
        "windows":{"offline":True,"sync":True,"reports":True,"takeoff":True},
        "android":{"offline":True,"sync":True,"reports":True,"takeoff":True},
        "telegram":{"offline":False,"sync":True,"reports":True,"takeoff":True},
    }
