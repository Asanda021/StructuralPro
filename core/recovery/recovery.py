"""Reliability and recovery primitives for StructuralPro persistence."""
from __future__ import annotations
import hashlib, json, sqlite3, time
from pathlib import Path
from typing import Any

class RecoveryError(RuntimeError): pass

def payload_checksum(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def backup_database(db_path: str | Path, backup_path: str | Path) -> dict[str, Any]:
    """Create a consistent backup atomically; preserve prior backups on failure."""
    import os
    import tempfile

    source_path = Path(db_path)
    target_path = Path(backup_path)
    if not source_path.is_file():
        raise RecoveryError("source database does not exist")
    if source_path.resolve() == target_path.resolve():
        raise RecoveryError("backup must not overwrite its source database")
    target_path.parent.mkdir(parents=True, exist_ok=True)

    temp_fd, temp_name = tempfile.mkstemp(
        prefix=f".{target_path.name}.", suffix=".tmp", dir=target_path.parent
    )
    os.close(temp_fd)
    temporary = Path(temp_name)
    source = None
    target = None
    try:
        source = sqlite3.connect(source_path.resolve().as_uri() + "?mode=ro", uri=True)
        target = sqlite3.connect(str(temporary))
        source.backup(target)
        target.commit()
        integrity = target.execute("PRAGMA integrity_check").fetchone()
        if not integrity or str(integrity[0]).lower() != "ok":
            raise RecoveryError("backup database failed SQLite integrity check")
        target.close()
        target = None
        source.close()
        source = None
        # Both connections are closed before replacing the backup. A failed
        # operation cannot truncate an existing recovery point.
        os.replace(temporary, target_path)
        return {
            "path": str(target_path), "size": target_path.stat().st_size,
            "created_at": time.time(),
        }
    finally:
        if target is not None:
            target.close()
        if source is not None:
            source.close()
        temporary.unlink(missing_ok=True)

def verify_database(db_path: str | Path) -> dict[str, Any]:
    source_path=Path(db_path)
    if not source_path.is_file(): raise RecoveryError("database does not exist")
    con=sqlite3.connect(source_path.resolve().as_uri()+"?mode=ro", uri=True)
    try:
        row=con.execute("PRAGMA integrity_check").fetchone()
        result=str(row[0]) if row else ""
        counts={}
        for table in ("projects","revisions"):
            counts[table]=int(con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        return {"ok":result.lower()=="ok","integrity_check":result,"counts":counts}
    finally: con.close()

def _canonical_project_payload(project: dict[str, Any]) -> str:
    return json.dumps(project, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def export_project(project: dict[str, Any], path: str | Path) -> dict[str, Any]:
    """Atomically export a checksummed, versioned offline project snapshot."""
    import os
    import tempfile

    if not isinstance(project, dict) or not str(project.get("id", "")).strip():
        raise RecoveryError("project must contain an id")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    envelope = {
        "format": "StructuralPro Project Backup",
        "schema_version": 2,
        "exported_at": time.time(),
        "project": project,
        "project_sha256": payload_checksum(_canonical_project_payload(project)),
    }
    raw = json.dumps(envelope, ensure_ascii=False, sort_keys=True, indent=2)
    fd, name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return {"path": str(target), "sha256": payload_checksum(raw), "bytes": len(raw.encode("utf-8"))}


def import_project(path: str | Path) -> dict[str, Any]:
    raw = Path(path).read_text(encoding="utf-8")
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RecoveryError("invalid backup JSON") from exc
    if not isinstance(envelope, dict):
        raise RecoveryError("invalid backup envelope")
    if envelope.get("format") != "StructuralPro Project Backup":
        raise RecoveryError("unsupported project backup format")
    version = envelope.get("schema_version")
    if type(version) is not int or version not in (1, 2):
        raise RecoveryError("unsupported project backup version")
    project = envelope.get("project")
    if not isinstance(project, dict) or not str(project.get("id", "")).strip():
        raise RecoveryError("backup does not contain a valid project")
    if version == 2:
        expected = envelope.get("project_sha256")
        if not isinstance(expected, str) or len(expected) != 64:
            raise RecoveryError("backup integrity checksum is missing or invalid")
        actual = payload_checksum(_canonical_project_payload(project))
        if not __import__("hmac").compare_digest(actual, expected):
            raise RecoveryError("project backup integrity checksum mismatch")
    # Version 1 remains readable for backward compatibility but did not have
    # cryptographic integrity evidence; only version 2 can detect payload edits.
    return project
