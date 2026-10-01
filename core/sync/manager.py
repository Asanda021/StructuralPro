"""Offline-first sync manager with deterministic queue processing."""
from __future__ import annotations
from core.sync.conflicts import merge_dict
class SyncManager:
    def __init__(self,provider=None,queue=None): self.provider=provider; self.queue=queue
    @property
    def online(self): return self.provider is not None
    def enqueue(self,record):
        if self.queue is None: raise RuntimeError("sync queue is not configured")
        return self.queue.push(record)
    def sync(self):
        if self.provider is None: return {"status":"offline","uploaded":0,"downloaded":0,"conflicts":[]}
        pending=self.queue.items() if self.queue else []
        uploaded=0
        for record in pending:
            self.provider.push(record); uploaded+=1
        if self.queue:
            self.queue.clear()
        return {"status":"synced","uploaded":uploaded,"downloaded":0,"conflicts":[]}
    @staticmethod
    def merge(base,local,remote): return merge_dict(base,local,remote)
