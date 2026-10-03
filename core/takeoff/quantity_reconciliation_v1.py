"""P411-P420 deterministic quantity reconciliation."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json, math
from typing import Sequence

@dataclass(frozen=True)
class QuantityEvidence:
    record_id: str
    source_id: str
    quantity: float
    unit: str
    revision: str
    status: str = "accepted"
    def validate(self):
        if not self.record_id or not self.source_id or not self.unit or not self.revision:
            raise ValueError("incomplete evidence")
        if not math.isfinite(float(self.quantity)) or self.quantity < 0:
            raise ValueError("quantity must be finite and non-negative")
        if self.status != "accepted":
            raise ValueError("only accepted evidence may reconcile")
        return self

class QuantityReconciler:
    @staticmethod
    def fingerprint(rows: Sequence[QuantityEvidence]) -> str:
        data=[r.validate().__dict__ for r in sorted(rows,key=lambda x:x.record_id)]
        return sha256(json.dumps(data,sort_keys=True,separators=(",",":")).encode()).hexdigest()

    def reconcile(self, rows: Sequence[QuantityEvidence]):
        for r in rows: r.validate()
        groups={}
        for r in rows:
            groups.setdefault((r.record_id,r.unit,r.revision),[]).append(r)
        out=[]
        for key, vals in sorted(groups.items()):
            sources=tuple(sorted({v.source_id for v in vals}))
            quantities=tuple(float(v.quantity) for v in vals)
            unique=set(quantities)
            out.append({
                "record_id":key[0],"unit":key[1],"revision":key[2],
                "sources":sources,"quantities":quantities,
                "status":"matched" if len(unique)==1 else "review"
            })
        return tuple(out)

    def duplicates(self, rows):
        seen={}
        for r in rows:
            r.validate()
            key=(r.record_id,r.revision,r.unit)
            seen.setdefault(key,[]).append(r.source_id)
        return tuple((k,tuple(sorted(v))) for k,v in sorted(seen.items()) if len(v)>1)
