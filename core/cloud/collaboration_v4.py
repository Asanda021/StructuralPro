"""P64 — resilient multi-user collaboration contract."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
ROLES={"owner","admin","editor","reviewer","viewer"}; OPS={"create","update","review","approve","archive","restore"}
@dataclass(frozen=True)
class Event:
    project_id:str; revision:int; actor_id:str; role:str; base_fingerprint:str; payload:dict; operation:str
def fingerprint(payload:dict)->str: return sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def validate_event(e:Event)->None:
    if not e.project_id or not e.actor_id or e.revision<1: raise ValueError("invalid event")
    if e.role not in ROLES or e.operation not in OPS: raise ValueError("invalid role/operation")
    if e.role=="viewer" and e.operation!="review": raise ValueError("viewer cannot mutate")
def apply_event(current_revision:int,current_fingerprint:str,e:Event)->dict:
    validate_event(e); fp=fingerprint(e.payload)
    if e.revision<=current_revision: return {"status":"stale_or_duplicate","accepted":False,"conflict":False}
    if e.base_fingerprint!=current_fingerprint: return {"status":"conflict","accepted":False,"conflict":True,"requires_review":True}
    return {"status":"accepted","accepted":True,"conflict":False,"revision":e.revision,"fingerprint":fp,"requires_review":e.operation=="review"}
def three_way(base:dict,local:dict,remote:dict)->dict:
    result=dict(base); conflicts=[]
    for k in set(base)|set(local)|set(remote):
        b,l,r=base.get(k),local.get(k),remote.get(k)
        if l==r: result[k]=l
        elif l==b: result[k]=r
        elif r==b: result[k]=l
        else: conflicts.append(k)
    return {"merged":result,"conflicts":sorted(conflicts),"requires_review":bool(conflicts)}
