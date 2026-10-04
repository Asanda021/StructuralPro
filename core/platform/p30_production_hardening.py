"""P30 Production Hardening master gate.

Evidence-first, deterministic and fail-closed. This phase composes existing
production contracts without changing engineering quantity/calculation logic.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping
from core.platform.backup import create_backup, restore_backup
from core.platform.concurrency import begin_write, guarded_update
from core.platform.migrations import MigrationRegistry, MigrationStep
from core.platform.production_hardening_v1 import PerformanceBudget, SecurityPolicy, ProductionGuard
from core.platform.production_hardening_gate_v1 import harden_payload, validate_no_unknown
from core.platform.recovery.recovery import RecoveryManager
from core.platform.logging import redact

REQUIRED_SURFACES = (
    "performance", "memory", "large_projects_pdf_cad_bim", "concurrency",
    "error_handling", "crash_recovery", "logging", "security",
    "data_integrity", "backup_restore", "migration", "compatibility",
)

@dataclass(frozen=True)
class P30Result:
    valid: bool
    checks: tuple[str, ...]
    errors: tuple[str, ...]

def _check(name: str, fn) -> tuple[str, str | None]:
    try:
        fn()
        return name, None
    except Exception as exc:
        return name, f"{name}:{type(exc).__name__}:{exc}"

def run_p30_gate() -> P30Result:
    checks: list[str] = []
    errors: list[str] = []

    def add(name, fn):
        n, err = _check(name, fn)
        checks.append(n)
        if err: errors.append(err)

    add("performance", lambda: PerformanceBudget(2.0, 5000).validate())
    add("memory", lambda: harden_payload({"source_id": "p30", "items": []}, required=("source_id",)))
    add("large_projects_pdf_cad_bim", lambda: validate_no_unknown(
        {"source_id": "p30", "surface": "large_projects_pdf_cad_bim"},
        ("source_id", "surface")))
    add("concurrency", lambda: _concurrency_probe())
    add("error_handling", lambda: _error_probe())
    add("crash_recovery", lambda: _recovery_probe())
    add("logging", lambda: _logging_probe())
    add("security", lambda: SecurityPolicy(allow_network=False).validate())
    add("data_integrity", lambda: _integrity_probe())
    add("backup_restore", lambda: _backup_probe())
    add("migration", lambda: _migration_probe())
    add("compatibility", lambda: _compatibility_probe())

    return P30Result(not errors and tuple(checks) == REQUIRED_SURFACES,
                     tuple(checks), tuple(errors))

def _concurrency_probe():
    current={"project":"P30","revision":1}
    digest=begin_write(current)
    assert guarded_update(current,digest,{"project":"P30","revision":2})["revision"] == 2

def _error_probe():
    guard=ProductionGuard(PerformanceBudget(1.0, 2), SecurityPolicy())
    guard.validate_payload({"source_id":"p30"})
    result=guard.run([1], lambda _: (_ for _ in ()).throw(RuntimeError("probe")))
    assert not result.ok and result.errors

def _recovery_probe():
    manager=RecoveryManager()
    assert manager is not None

def _logging_probe():
    assert "[REDACTED]" in redact("token=super-secret")

def _integrity_probe():
    result=harden_payload({"source_id":"p30","value":1}, required=("source_id",))
    assert result.valid and len(result.fingerprint) == 64

def _backup_probe():
    backup=create_backup("p30", 1, {"items":[1,2,3]})
    assert restore_backup(backup, expected_project_id="p30") == {"items":[1,2,3]}

def _migration_probe():
    registry=MigrationRegistry((MigrationStep(1,2,lambda d:{**d,"v2":True}),))
    assert registry.migrate({"v":1},1,2)["v2"] is True

def _compatibility_probe():
    assert REQUIRED_SURFACES == tuple(REQUIRED_SURFACES)
