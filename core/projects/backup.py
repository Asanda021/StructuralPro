"""Atomic project backup and recovery helpers."""
from __future__ import annotations
import json, shutil, time
from pathlib import Path

class BackupManager:
    def __init__(self, root: str|Path):
        self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True)
    def create(self, project: dict, project_id: str):
        stamp=time.strftime("%Y%m%d_%H%M%S")
        path=self.root/f"{project_id}_{stamp}.json"
        tmp=path.with_suffix(".tmp")
        tmp.write_text(json.dumps(project,ensure_ascii=False,indent=2),encoding="utf-8")
        tmp.replace(path)
        return path
    def list(self, project_id: str):
        return sorted(self.root.glob(f"{project_id}_*.json"), reverse=True)
    def restore(self, path: str|Path):
        return json.loads(Path(path).read_text(encoding="utf-8"))
    def prune(self, project_id: str, keep=10):
        files=self.list(project_id)
        for p in files[max(1,int(keep)):]: p.unlink(missing_ok=True)
        return files[:max(1,int(keep))]
