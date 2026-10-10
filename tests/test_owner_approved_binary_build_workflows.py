"""Prevent accidental re-enabling of unapproved executable/installer builds.

Static contract only; GitHub permission and workflow execution still need review.
"""
from pathlib import Path
import re

import pytest


ROOT = Path(__file__).resolve().parents[1]
BUILD_WORKFLOWS = (
    ".github/workflows/windows-release.yml",
    ".github/workflows/edition-builds.yml",
    ".github/workflows/android-build.yml",
    ".github/workflows/p37-real-product-deployment.yml",
)


@pytest.mark.parametrize("relative_path", BUILD_WORKFLOWS)
def test_binary_build_requires_explicit_owner_dispatch(relative_path):
    source = (ROOT / relative_path).read_text(encoding="utf-8")
    assert re.search(r"(?m)^on:\s*$", source)
    assert re.search(r"(?m)^  workflow_dispatch:\s*$", source)
    assert not re.search(r"(?m)^  (?:push|pull_request|pull_request_target|schedule|release|workflow_run|workflow_call|repository_dispatch|create):", source)
    assert re.search(r"(?m)^      build_approved:\s*$", source)
    assert re.search(r"(?m)^        default: false\s*$", source)
    assert "github.event_name == 'workflow_dispatch'" in source
    assert "github.actor == 'Asanda021'" in source
    assert "inputs.build_approved == true" in source
    assert re.search(r"(?m)^    if: .*github.actor.*build_approved", source)


def test_every_binary_producer_has_an_owner_approval_gate():
    """Catch newly introduced packaging workflows, not only the known four."""
    workflow_dir = ROOT / ".github" / "workflows"
    production_commands = (
        "packaging/build_windows.ps1",
        "packaging/build_windows_edition.ps1",
        "ISCC.exe",
        ":app:assembleRelease",
        "softprops/action-gh-release@",
    )
    approved = set(BUILD_WORKFLOWS)
    for path in sorted(workflow_dir.glob("*.yml")):
        content = path.read_text(encoding="utf-8")
        if any(command in content for command in production_commands):
            assert path.relative_to(ROOT).as_posix() in approved, (
                f"Unapproved binary/release producer: {path.name}"
            )
