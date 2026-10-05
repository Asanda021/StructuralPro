"""Deterministic BIM/Digital Twin graph for P191-P200."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable

KINDS={"source","bim_object","drawing_evidence","quantity","boq","estimate"}
@dataclass(frozen=True)
class TwinNode:
    node_id:str; kind:str; external_id:str
    quantity:float|None=None
    def validate(self):
        if self.kind not in KINDS or not self.node_id.strip() or not self.external_id.strip(): raise ValueError("invalid twin node")
        if self.kind=="quantity" and (self.quantity is None or self.quantity<0): raise ValueError("explicit quantity required")
        if self.kind!="quantity" and self.quantity is not None: raise ValueError("quantity only allowed on quantity nodes")
        return self
@dataclass(frozen=True)
class TwinEdge:
    edge_id:str; src:str; dst:str; relation:str
    def validate(self):
        if not all(x.strip() for x in (self.edge_id,self.src,self.dst,self.relation)): raise ValueError("invalid twin edge")
        return self
class DigitalTwinGraph:
    def __init__(self,nodes:Iterable[TwinNode]=(),edges:Iterable[TwinEdge]=()):
        self.nodes=tuple(nodes); self.edges=tuple(edges)
        self.validate()
    @staticmethod
    def ident(kind,external_id):
        return "twin-"+sha256(f"{kind}|{external_id}".encode()).hexdigest()[:16]
    @staticmethod
    def edge_ident(src,dst,relation):
        return "edge-"+sha256(f"{src}|{dst}|{relation}".encode()).hexdigest()[:16]
    def validate(self):
        for n in self.nodes: n.validate()
        ids=[n.node_id for n in self.nodes]
        if len(ids)!=len(set(ids)): raise ValueError("duplicate node identity")
        known=set(ids)
        for e in self.edges:
            e.validate()
            if e.src not in known or e.dst not in known: raise ValueError("edge references unknown node")
        return self
    def fingerprint(self):
        payload="|".join(sorted(f"N:{n.node_id}:{n.kind}:{n.external_id}:{n.quantity}" for n in self.nodes)+sorted(f"E:{e.edge_id}:{e.src}:{e.dst}:{e.relation}" for e in self.edges))
        return sha256(payload.encode()).hexdigest()
    def impacts(self, changed_ids:set[str]):
        adj={}
        for e in self.edges: adj.setdefault(e.src,set()).add(e.dst)
        seen=set(changed_ids); queue=sorted(changed_ids)
        while queue:
            cur=queue.pop(0)
            for nxt in sorted(adj.get(cur,())):
                if nxt not in seen: seen.add(nxt); queue.append(nxt)
        return tuple(sorted(seen))
