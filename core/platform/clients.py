"""Shared platform contract used by Windows, Android and Telegram clients."""
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
        self.session=ClientSession(platform)
        self.project_service=project_service

    def open_project(self, project_id: str):
        self.session.project_id=str(project_id)
        if self.project_service: return self.project_service(project_id)
        return {"id":str(project_id),"platform":self.session.platform}

    def state(self)->dict[str,Any]:
        return {"platform":self.session.platform,"project_id":self.session.project_id,"offline":self.session.offline}
