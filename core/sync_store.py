"""Atomic JSON persistence for the offline sync outbox."""
from pathlib import Path
import json
from .sync_engine import SyncRecord
class JsonSyncStore:
    def __init__(self,path): self.path=Path(path)
    def save(self,records):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        temp=self.path.with_suffix(self.path.suffix+".tmp")
        temp.write_text(json.dumps([r.to_dict() for r in records],ensure_ascii=False,sort_keys=True),encoding="utf-8")
        temp.replace(self.path)
    def load(self):
        if not self.path.exists(): return []
        value=json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(value,list): raise ValueError("sync store must contain a list")
        return [SyncRecord.from_dict(x) for x in value]
