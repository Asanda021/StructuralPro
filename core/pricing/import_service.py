"""Fail-closed price-list import with provenance and user-import support."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from core.pricing.catalog import PriceCatalog
from core.pricing.source_registry import PriceSource, PriceSourceRegistry


@dataclass(frozen=True)
class ImportReceipt:
    source_id: str
    year: int
    discipline: str
    filename: str
    sha256: str
    rows: int
    verified_source: bool
    imported_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class PricebookImportService:
    """Import official/user datasets without ever inventing source provenance."""

    def __init__(self, catalog: PriceCatalog | None = None, registry: PriceSourceRegistry | None = None):
        self.catalog = catalog or PriceCatalog()
        self.registry = registry or PriceSourceRegistry()

    def inspect(self, path: str | Path, *, year: int, discipline: str = "building",
                source_id: str = "user-import") -> dict[str, Any]:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(p)
        text = p.read_text(encoding="utf-8-sig")
        source = self.registry.get(year, discipline, source_id)
        validation = self.registry.validate_import(
            source or PriceSource(year, discipline, "User supplied dataset", "User", source_id),
            text,
        )
        return {
            "path": str(p),
            "filename": p.name,
            "year": year,
            "discipline": discipline,
            "source_id": source_id,
            "sha256": validation["sha256"],
            "rows": validation["rows"],
            "valid": validation["valid"],
            "errors": validation["errors"],
            "verified_source": bool(source and source.verified and
                                    self.registry.verify_record(source, validation["sha256"])),
        }

    def import_file(self, path: str | Path, *, year: int, discipline: str = "building",
                    source_id: str = "user-import", require_verified_source: bool = False) -> ImportReceipt:
        info = self.inspect(path, year=year, discipline=discipline, source_id=source_id)
        if not info["valid"]:
            raise ValueError("price-list validation failed: " + "; ".join(info["errors"][:5]))
        if require_verified_source and not info["verified_source"]:
            raise PermissionError(
                "Official/verified import requires a registered source and matching SHA-256; "
                "user-import mode remains available."
            )
        text = Path(path).read_text(encoding="utf-8-sig")
        imported = self.catalog.import_csv(text, replace_year=False)
        return ImportReceipt(
            source_id=source_id,
            year=year,
            discipline=discipline,
            filename=Path(path).name,
            sha256=sha256(text.encode("utf-8")).hexdigest(),
            rows=imported,
            verified_source=info["verified_source"],
            imported_at=datetime.now(timezone.utc).isoformat(),
        )
