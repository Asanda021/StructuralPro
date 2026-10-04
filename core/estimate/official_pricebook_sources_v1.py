"""Official Iranian pricebook source registry.
Sources point to the Planning and Budget Organization / SAMA publication system.
Raw files are not embedded until their bytes are actually retrieved and hashed.
"""
from dataclasses import dataclass
from hashlib import sha256

@dataclass(frozen=True)
class OfficialPricebookSource:
    year:int
    discipline:str
    title:str
    official_url:str
    document_type:str
    circular_date:str

SOURCES=(
    OfficialPricebookSource(1402,"ابنیه","فهرست بهای واحد پایه رشته ابنیه سال ۱۴۰۲",
        "https://sama.mporg.ir/","official-publication-portal",""),
    OfficialPricebookSource(1404,"ابنیه","فهرست بهای واحد پایه رشته ابنیه سال ۱۴۰۴",
        "https://sama.mporg.ir/DigitalAsset/DigitalAsset/FehrestBaha1404.rar?Web=1","official-publication-archive","1403/12/29"),
)

def validate_sources():
    if not SOURCES: raise ValueError("official sources required")
    for s in SOURCES:
        if s.discipline!="ابنیه" or not s.official_url.startswith("https://"):
            raise ValueError("invalid official source")
    return True

def registry_fingerprint():
    validate_sources()
    raw="|".join(f"{s.year}|{s.discipline}|{s.title}|{s.official_url}|{s.document_type}|{s.circular_date}" for s in SOURCES)
    return sha256(raw.encode()).hexdigest()
