"""Priority 23 recovery regression tests."""
import json, sqlite3
import pytest
from core.projects.store import ProjectStore
from core.recovery.recovery import backup_database, verify_database, export_project, import_project, RecoveryError

def test_database_backup_and_integrity(tmp_path):
    db=tmp_path/"projects.db"; store=ProjectStore(db)
    store.save("P23",{"id":"P23","name":"Recovery"})
    backup=tmp_path/"backup.db"; info=backup_database(db,backup)
    assert info["size"]>0 and verify_database(db)["ok"]
    restored=sqlite3.connect(backup)
    assert restored.execute("select count(*) from projects").fetchone()[0]==1
    restored.close(); store.close()

def test_project_export_import_roundtrip(tmp_path):
    project={"id":"P23","name":"Demo","takeoffs":[{"id":"1"}]}
    path=tmp_path/"P23.spbackup.json"
    info=export_project(project,path)
    assert len(info["sha256"])==64
    assert import_project(path)==project

def test_invalid_backup_is_rejected(tmp_path):
    p=tmp_path/"bad.json"; p.write_text(json.dumps({"format":"wrong"}),encoding="utf-8")
    try: import_project(p); assert False
    except RecoveryError: pass


def test_backup_replaces_existing_database_only_after_successful_verification(tmp_path):
    db = tmp_path / "projects.db"
    store = ProjectStore(db)
    store.save("first", {"id": "first", "name": "قبل"})
    target = tmp_path / "backup.db"
    backup_database(db, target)
    with sqlite3.connect(target) as before:
        assert before.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 1
    store.save("second", {"id": "second", "name": "بعد"})
    backup_database(db, target)
    with sqlite3.connect(target) as after:
        assert after.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 2
    assert not list(tmp_path.glob(".backup.db.*.tmp"))
    store.close()


def test_failed_sqlite_backup_preserves_existing_recovery_point(tmp_path):
    damaged = tmp_path / "broken.db"
    damaged.write_bytes(b"not-a-sqlite-database")
    existing = tmp_path / "recovery.db"
    existing.write_bytes(b"previous-known-good-backup")
    with pytest.raises((sqlite3.DatabaseError, RecoveryError)):
        backup_database(damaged, existing)
    assert existing.read_bytes() == b"previous-known-good-backup"
    assert not list(tmp_path.glob(".recovery.db.*.tmp"))


def test_source_and_destination_cannot_be_same_database(tmp_path):
    db = tmp_path / "projects.db"
    store = ProjectStore(db)
    store.save("first", {"id": "first", "name": "قبل"})
    with pytest.raises(RecoveryError, match="source database"):
        backup_database(db, db)
    assert verify_database(db)["ok"] is True
    store.close()


def test_versioned_project_export_detects_tampering_and_preserves_existing_file(tmp_path):
    project = {"id": "P23", "name": "پروژه فارسی", "boq": [{"quantity": 10}]}
    target = tmp_path / "project.json"
    export_project(project, target)
    saved = json.loads(target.read_text(encoding="utf-8"))
    assert saved["schema_version"] == 2
    assert len(saved["project_sha256"]) == 64
    assert import_project(target) == project
    saved["project"]["boq"][0]["quantity"] = 999
    target.write_text(json.dumps(saved, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(RecoveryError, match="checksum mismatch"):
        import_project(target)


def test_new_export_failure_does_not_truncate_prior_backup(tmp_path):
    target = tmp_path / "project.json"
    export_project({"id": "P23", "name": "old"}, target)
    previous = target.read_bytes()
    with pytest.raises(TypeError):
        export_project({"id": "P23", "name": "new", "bad": {1, 2, 3}}, target)
    assert target.read_bytes() == previous
    assert not list(tmp_path.glob(".project.json.*.tmp"))


def test_legacy_project_export_is_readable_without_false_integrity_claim(tmp_path):
    target = tmp_path / "legacy.json"
    project = {"id": "legacy", "name": "legacy-before-checksum"}
    target.write_text(json.dumps({
        "format": "StructuralPro Project Backup", "schema_version": 1,
        "project": project,
    }), encoding="utf-8")
    assert import_project(target) == project


def test_invalid_json_backup_envelope_is_rejected_cleanly(tmp_path):
    target = tmp_path / "bad.json"
    target.write_text('[]', encoding="utf-8")
    with pytest.raises(RecoveryError, match="envelope"):
        import_project(target)
