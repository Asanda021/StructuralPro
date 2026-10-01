"""Deterministic offline conflict resolution for project records."""
from __future__ import annotations
from copy import deepcopy
from typing import Any

def merge_dict(base: dict[str,Any], local: dict[str,Any], remote: dict[str,Any]) -> tuple[dict[str,Any],list[str]]:
    out=deepcopy(base); conflicts=[]
    keys=set(base)|set(local)|set(remote)
    for k in sorted(keys):
        b,l,r=base.get(k),local.get(k),remote.get(k)
        if l==r: out[k]=deepcopy(l)
        elif l==b: out[k]=deepcopy(r)
        elif r==b: out[k]=deepcopy(l)
        else:
            conflicts.append(k)
            # Preserve both values without silent loss.
            out[k]={"_conflict":{"local":deepcopy(l),"remote":deepcopy(r),"base":deepcopy(b)}}
    return out,conflicts

def resolve_conflicts(project: dict[str,Any], choices: dict[str,str]) -> dict[str,Any]:
    out=deepcopy(project)
    for key,choice in choices.items():
        value=out.get(key)
        if isinstance(value,dict) and "_conflict" in value:
            c=value["_conflict"]
            if choice not in {"local","remote","base"}: raise ValueError("choice must be local, remote or base")
            out[key]=deepcopy(c[choice])
    return out
