"""BIM/CAD deep integration boundary for StructuralPro.

Provides a deterministic, format-neutral model registry that connects IFC/DWG/DXF
sources to canonical takeoff rows while preserving revision, provenance, units,
mapping status and duplicate safety. No CAD/BIM calculation engine is required.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Iterable
from pathlib import Path
import hashlib, math


SUPPORTED_FORMATS = {"ifc", "dwg", "dxf", "pdf"}
SUPPORTED_STATUS = {"registered", "processed", "superseded", "rejected"}


def _text(v: Any) -> str:
    return " ".join(str(v or "").strip().split())


def _nonnegative(v: Any, label: str) -> float:
    x = float(v)
    if not math.isfinite(x) or x < 0:
        raise ValueError(f"{label} must be finite and non-negative")
    return x


@dataclass(frozen=True)
class ModelSource:
    id: str
    path: str
    format: str
    revision: str = "1"
    discipline: str = ""
    status: str = "registered"
    sha256: str = ""
    units: str = ""


@dataclass(frozen=True)
class ModelObject:
    source_id: str
    object_id: str
    object_type: str
    name: str = ""
    level: str = ""
    layer: str = ""
    properties: dict[str, Any] | None = None
    quantities: dict[str, float] | None = None


class ModelRegistry:
    def __init__(self, *, sources: Iterable[ModelSource] = (), objects: Iterable[ModelObject] = ()):
        self.sources = list(sources)
        self.objects = list(objects)
        self.validate()

    @staticmethod
    def fingerprint(path: str | Path) -> str:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(p)
        h = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def validate(self) -> "ModelRegistry":
        source_ids = set()
        for s in self.sources:
            sid = _text(s.id)
            if not sid or sid in source_ids:
                raise ValueError(f"duplicate/empty model source id: {sid}")
            source_ids.add(sid)
            if _text(s.format).lower() not in SUPPORTED_FORMATS:
                raise ValueError(f"unsupported model format: {s.format}")
            if s.status not in SUPPORTED_STATUS:
                raise ValueError(f"invalid model source status: {s.status}")
            if not _text(s.revision):
                raise ValueError("model revision is required")
        object_keys = set()
        for o in self.objects:
            if o.source_id not in source_ids:
                raise ValueError(f"unknown model source: {o.source_id}")
            oid = _text(o.object_id)
            key = (o.source_id, oid)
            if not oid or key in object_keys:
                raise ValueError(f"duplicate/empty model object id: {o.source_id}:{oid}")
            object_keys.add(key)
            for value in (o.quantities or {}).values():
                _nonnegative(value, "model quantity")
        return self

    def register_source(self, source: ModelSource) -> ModelSource:
        if any(s.id == source.id for s in self.sources):
            raise ValueError(f"duplicate model source: {source.id}")
        self.sources.append(source)
        try:
            self.validate()
        except Exception:
            self.sources.pop()
            raise
        return source

    def add_object(self, obj: ModelObject) -> ModelObject:
        if any(o.source_id == obj.source_id and o.object_id == obj.object_id for o in self.objects):
            raise ValueError(f"duplicate model object: {obj.source_id}:{obj.object_id}")
        self.objects.append(obj)
        try:
            self.validate()
        except Exception:
            self.objects.pop()
            raise
        return obj

    def source_inventory(self) -> dict[str, Any]:
        by_format: dict[str, int] = {}
        by_revision: dict[str, int] = {}
        for s in self.sources:
            by_format[s.format] = by_format.get(s.format, 0) + 1
            by_revision[s.revision] = by_revision.get(s.revision, 0) + 1
        return {"sources": len(self.sources), "objects": len(self.objects),
                "by_format": by_format, "by_revision": by_revision}

    def objects_for_source(self, source_id: str) -> list[ModelObject]:
        return [o for o in self.objects if o.source_id == source_id]

    def revision_diff(self, old_revision: str, new_revision: str) -> dict[str, Any]:
        old = {(o.object_id, o.object_type): o for o in self.objects
               if next((s.revision for s in self.sources if s.id == o.source_id), None) == old_revision}
        new = {(o.object_id, o.object_type): o for o in self.objects
               if next((s.revision for s in self.sources if s.id == o.source_id), None) == new_revision}
        added = sorted(set(new) - set(old))
        removed = sorted(set(old) - set(new))
        changed = []
        for key in sorted(set(old) & set(new)):
            a, b = old[key], new[key]
            if (a.name, a.level, a.layer, a.properties, a.quantities) != (b.name, b.level, b.layer, b.properties, b.quantities):
                changed.append({"object_id": key[0], "object_type": key[1]})
        return {"old_revision": old_revision, "new_revision": new_revision,
                "added": [dict(object_id=k[0], object_type=k[1]) for k in added],
                "removed": [dict(object_id=k[0], object_type=k[1]) for k in removed],
                "changed": changed}

    def to_takeoff_rows(self, *, mapping: dict[str, str] | None = None,
                        source_id: str | None = None, require_mapping: bool = False) -> dict[str, Any]:
        mapping = mapping or {}
        rows = []
        unmapped = []
        selected = self.objects if source_id is None else self.objects_for_source(source_id)
        for o in selected:
            code = mapping.get(o.object_type)
            if not code:
                unmapped.append(o.object_id)
                if require_mapping:
                    continue
            for key, value in (o.quantities or {}).items():
                unit = {"Length": "m", "Area": "m2", "Volume": "m3", "Count": "عدد"}.get(key, "")
                rows.append({
                    "source": f"model:{o.source_id}:{o.object_id}:{key}",
                    "source_id": o.source_id,
                    "object_id": o.object_id,
                    "object_type": o.object_type,
                    "level": o.level,
                    "layer": o.layer,
                    "description": o.name or o.object_type,
                    "quantity": _nonnegative(value, "model quantity"),
                    "unit": unit,
                    "price_code": code,
                    "mapping_status": "mapped" if code else "unmapped",
                    "needs_confirmation": not bool(code),
                })
        return {"rows": rows, "unmapped": unmapped}

    def duplicate_objects(self) -> list[str]:
        seen = set()
        duplicates = []
        for o in self.objects:
            key = (o.object_id, o.object_type)
            if key in seen:
                duplicates.append(f"{o.source_id}:{o.object_id}")
            seen.add(key)
        return duplicates

    def export_dict(self) -> dict[str, Any]:
        return {"sources": [asdict(s) for s in self.sources],
                "objects": [asdict(o) for o in self.objects]}
