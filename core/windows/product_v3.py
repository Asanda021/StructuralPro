"""P64 — production-grade Windows desktop contract."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
@dataclass(frozen=True)
class WindowsRelease:
    version:str; installer:str; executable:str; sha256:str; architecture:str; channel:str; min_windows:str
@dataclass(frozen=True)
class WindowsWorkspace:
    project_extension:str; backup_extension:str; autosave_interval_seconds:int; recovery_enabled:bool; offline_enabled:bool
def validate_release(r:WindowsRelease)->None:
    if not all((r.version,r.installer,r.executable,r.sha256,r.architecture,r.min_windows)) or len(r.sha256)!=64: raise ValueError("incomplete Windows release")
    if r.architecture not in {"x64","arm64"} or r.channel not in {"stable","beta"}: raise ValueError("unsupported Windows release")
def validate_workspace(w:WindowsWorkspace)->None:
    if not w.project_extension.startswith(".") or not w.backup_extension.startswith(".") or w.autosave_interval_seconds<5 or not w.recovery_enabled or not w.offline_enabled: raise ValueError("unsafe workspace")
def release_manifest(r:WindowsRelease,w:WindowsWorkspace)->dict:
    validate_release(r); validate_workspace(w)
    return {"platform":"windows","architecture":r.architecture,"version":r.version,"installer":r.installer,"executable":r.executable,"sha256":r.sha256,"channel":r.channel,"min_windows":r.min_windows,"workspace":w.__dict__,"install":{"clean_install":True,"upgrade":True,"rollback":True,"uninstall":True}}
def manifest_fingerprint(manifest:dict)->str:
    return sha256(json.dumps(manifest,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
