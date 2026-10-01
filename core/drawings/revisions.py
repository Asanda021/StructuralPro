from __future__ import annotations
from typing import Any, Iterable

def compare(old: Iterable[Any], new: Iterable[Any]) -> dict[str,Any]:
    def key(x):
        if hasattr(x,"handle"): return str(x.handle)
        if isinstance(x,dict): return str(x.get("handle") or x.get("id") or x)
        return str(x)
    a={key(x):x for x in old}; b={key(x):x for x in new}
    return {"added":[b[k] for k in b.keys()-a.keys()],"removed":[a[k] for k in a.keys()-b.keys()],"unchanged":[b[k] for k in a.keys()&b.keys()]}
