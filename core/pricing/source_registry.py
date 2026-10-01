"""Verified price-list source registry.
It records provenance and licensing; it never fabricates official prices.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
from pathlib import Path

@dataclass(frozen=True)
class PriceSource:
    year:int
    group:str
    source_name:str
    source_url:str
    license_note:str
    retrieved_at:str
    sha256:str
    verified:bool=False

class PriceSourceRegistry:
    def __init__(self,sources=None): self.sources=list(sources or [])
    def add(self,source:PriceSource): self.sources.append(source)
    def verify_record(self,source:PriceSource,sha256:str)->bool: return source.sha256==sha256
    def export(self,path):
        Path(path).write_text(json.dumps([asdict(x) for x in self.sources],ensure_ascii=False,indent=2),encoding="utf-8")
    @staticmethod
    def now(): return datetime.now(timezone.utc).isoformat()
