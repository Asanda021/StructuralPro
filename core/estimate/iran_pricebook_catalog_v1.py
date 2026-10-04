from dataclasses import dataclass
from hashlib import sha256

@dataclass(frozen=True)
class PricebookSource:
    discipline: str
    year: int
    title: str
    source: str
    format: str
    verified_at: str

def validate(sources):
    if not sources: raise ValueError("pricebook sources required")
    seen=set()
    for s in sources:
        if s.discipline!="ابنیه": raise ValueError("unsupported discipline")
        if s.year < 1300 or s.year > 1500: raise ValueError("invalid year")
        if not all((s.title,s.source,s.format,s.verified_at)): raise ValueError("incomplete source")
        k=(s.discipline,s.year,s.format)
        if k in seen: raise ValueError("duplicate pricebook source")
        seen.add(k)

def fingerprint(sources):
    validate(sources)
    p="|".join(sorted(f"{s.discipline}|{s.year}|{s.title}|{s.source}|{s.format}|{s.verified_at}" for s in sources))
    return sha256(p.encode()).hexdigest()
