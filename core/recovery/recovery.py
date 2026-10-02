"""Reliability and recovery primitives for StructuralPro persistence."""
from __future__ import annotations
import hashlib, json, sqlite3, time
from pathlib import Path
from typing import Any

class RecoveryError(RuntimeError): pass

def payload_checksum(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def backup_database(db_path: str | Path, backup_path: str | Path) -> dict[str, Any]:
    source=sqlite3.connect(str(db_path))
    target_path=Path(backup_path); target_path.parent.mkdir(parents=True,exist_ok=True)
    target=sqlite3.connect(str(target_path))
    try:
        source.backup(target)
        target.commit()
    finally:
        target.close(); source.close()
    return {"path":str(target_path),"size":target_path.stat().st_size,"created_at":time.time()}

def verify_database(db_path: str | Path) -> dict[str, Any]:
    con=sqlite3.connect(str(db_path))
    try:
        row=con.execute("PRAGMA integrity_check").fetchone()
        result=str(row[0]) if row else ""
        counts={}
        for table in ("projects","revisions"):
            counts[table]=int(con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        return {"ok":result.lower()=="ok","integrity_check":result,"counts":counts}
    finally: con.close()

def export_project(project: dict[str, Any], path: str | Path) -> dict[str, Any]:
    if not isinstance(project,dict) or not project.get("id"):
        raise RecoveryError("project must contain an id")
    target=Path(path); target.parent.mkdir(parents=True,exist_ok=True)
    envelope={"format":"StructuralPro Project Backup","schema_version":1,
              "exported_at":time.time(),"project":project}
    raw=json.dumps(envelope,ensure_ascii=False,sort_keys=True,indent=2)
    target.write_text(raw,encoding="utf-8")
    return {"path":str(target),"sha256":payload_checksum(raw),"bytes":len(raw.encode("utf-8"))}

def import_project(path: str | Path) -> dict[str, Any]:
    raw=Path(path).read_text(encoding="utf-8")
    try: envelope=json.loads(raw)
    except json.JSONDecodeError as exc: raise RecoveryError("invalid backup JSON") from exc
    if envelope.get("format")!="StructuralPro Project Backup" or envelope.get("schema_version")!=1:
        raise RecoveryError("unsupported project backup format")
    project=envelope.get("project")
    if not isinstance(project,dict) or not str(project.get("id","")).strip():
        raise RecoveryError("backup does not contain a valid project")
    return project
