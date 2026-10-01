"""Offline-first sync manager with deterministic conflict reporting."""
from __future__ import annotations
from .offline_queue import OfflineQueue
from .contracts import SyncResult
class SyncManager:
    def __init__(self,provider=None,queue=None):
        self.provider=provider; self.queue=queue
    def record_local_change(self,record):
        if self.queue: self.queue.enqueue(record)
    def sync(self,project_id):
        if not self.provider: return SyncResult(0,0,0,["no_sync_provider"])
        local=self.queue.peek() if self.queue else []
        pushed=0; errors=[]
        try:
            if local:
                self.provider.push(local); pushed=len(local)
                if self.queue: self.queue.clear()
            pulled=self.provider.pull(project_id) or []
            return SyncResult(pushed,len(pulled),0,errors)
        except Exception as exc:
            return SyncResult(pushed,0,0,[str(exc)])
