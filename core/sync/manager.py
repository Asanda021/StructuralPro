"""Offline-first synchronization manager."""
from __future__ import annotations
from core.sync.conflicts import merge_dict
from core.sync.contracts import SyncResult

class SyncManager:
    def __init__(self,provider=None,queue=None):
        self.provider=provider; self.queue=queue
    @property
    def online(self): return self.provider is not None
    def record_local_change(self,record): return self.enqueue(record)
    def enqueue(self,record):
        if self.queue is None: raise RuntimeError("sync queue is not configured")
        return self.queue.enqueue(record)
    def sync(self,project_id=None):
        if self.provider is None:
            return SyncResult(0,0,0,["no_sync_provider"])
        pending=self.queue.peek() if self.queue else []
        if project_id is not None:
            pending=[r for r in pending if str(r.get("project_id"))==str(project_id)]
        pushed=0
        if pending:
            result=self.provider.push(pending); pushed=int(result.get("pushed",len(pending)))
        pulled=len(self.provider.pull(project_id)) if project_id is not None else 0
        if self.queue and pending:
            remaining=[r for r in self.queue.peek() if r not in pending]
            if remaining: self.queue.path.write_text(__import__("json").dumps(remaining,ensure_ascii=False),encoding="utf-8")
            else: self.queue.clear()
        return SyncResult(pushed,pulled,0,[])
    @staticmethod
    def merge(base,local,remote): return merge_dict(base,local,remote)
