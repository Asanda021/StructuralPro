"""Release metadata and offline license primitives for StructuralPro."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
VERSION_FILE = ROOT / "VERSION"

def load_version() -> str:
    value = VERSION_FILE.read_text(encoding="utf-8").strip()
    parts = value.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise ValueError("VERSION must use MAJOR.MINOR.PATCH")
    return value

@dataclass(frozen=True)
class ReleaseInfo:
    name: str
    version: str
    channel: str = "stable"
    def as_dict(self) -> dict[str, str]:
        return {"name": self.name, "version": self.version, "channel": self.channel}

@dataclass(frozen=True)
class LicenseRecord:
    product: str
    license_id: str
    customer: str
    expires_on: str = ""
    features: tuple[str, ...] = ()
    issuer: str = ""
    def payload(self) -> dict:
        return {
            "product": self.product,
            "license_id": self.license_id,
            "customer": self.customer,
            "expires_on": self.expires_on,
            "features": list(self.features),
            "issuer": self.issuer,
        }
    def canonical_bytes(self) -> bytes:
        return json.dumps(self.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    def fingerprint(self) -> str:
        return sha256(self.canonical_bytes()).hexdigest()

class LicenseVerifier:
    """Injected verifier boundary; private signing material never belongs here."""
    def __init__(self, verify_signature: Callable[[bytes, str], bool], expected_product: str = "StructuralPro"):
        self._verify_signature = verify_signature
        self._expected_product = expected_product

    def verify(self, record: LicenseRecord, signature: str) -> bool:
        if record.product != self._expected_product or not record.license_id or not record.customer:
            return False
        if not signature or not record.issuer:
            return False
        try:
            return bool(self._verify_signature(record.canonical_bytes(), signature))
        except Exception:
            return False
