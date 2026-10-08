"""Authorized external DWG conversion provider.

StructuralPro does not bundle or link a native DWG parser. This adapter invokes
an explicitly installed/authorized command-line converter and then routes the
result through the existing real DXF parser.

The default command contract matches ODA File Converter's documented CLI shape:
  converter <source_dir> <target_dir> <output_version> <output_type> <audit> <recursive>

The executable is never downloaded, guessed, or silently replaced.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Sequence

from core.cad.ezdxf_provider_v1 import DXFDocumentEvidence, read_dxf


class DWGProviderError(ValueError):
    """Raised when an authorized DWG provider cannot produce verified DXF evidence."""


@dataclass(frozen=True)
class DWGConverterConfig:
    executable: str
    output_version: str = "ACAD2018"
    audit: bool = True
    recursive: bool = False
    timeout_seconds: int = 120


class ExternalDWGConverterProvider:
    """Convert DWG to DXF through an explicitly configured external provider."""

    def __init__(self, config: DWGConverterConfig) -> None:
        if not config.executable.strip():
            raise DWGProviderError("DWG converter executable is required")
        if config.timeout_seconds <= 0:
            raise DWGProviderError("DWG converter timeout must be positive")
        self.config = config

    def _resolve_executable(self) -> str:
        resolved = shutil.which(self.config.executable)
        if resolved:
            return resolved
        candidate = Path(self.config.executable)
        if candidate.is_file():
            return str(candidate)
        raise DWGProviderError(
            "Configured DWG converter was not found. Install an authorized provider "
            "and configure its executable path."
        )

    def _command(
        self,
        executable: str,
        source_dir: Path,
        target_dir: Path,
    ) -> Sequence[str]:
        return (
            executable,
            str(source_dir),
            str(target_dir),
            self.config.output_version,
            "DXF",
            "1" if self.config.audit else "0",
            "1" if self.config.recursive else "0",
        )

    def convert(self, source: str | Path) -> Path:
        input_path = Path(source)
        if input_path.suffix.lower() != ".dwg":
            raise DWGProviderError("DWG converter accepts .dwg only")
        if not input_path.is_file():
            raise DWGProviderError("DWG source file does not exist")

        executable = self._resolve_executable()
        with tempfile.TemporaryDirectory(prefix="structuralpro-dwg-") as temp:
            source_dir = Path(temp) / "input"
            target_dir = Path(temp) / "output"
            source_dir.mkdir()
            target_dir.mkdir()
            staged = source_dir / input_path.name
            staged.write_bytes(input_path.read_bytes())

            try:
                result = subprocess.run(
                    self._command(executable, source_dir, target_dir),
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=self.config.timeout_seconds,
                )
            except subprocess.TimeoutExpired as exc:
                raise DWGProviderError("DWG conversion timed out") from exc
            except OSError as exc:
                raise DWGProviderError(f"DWG converter could not be executed: {exc}") from exc

            if result.returncode != 0:
                detail = (result.stderr or result.stdout or "no converter diagnostics").strip()
                raise DWGProviderError(
                    f"DWG conversion failed with exit code {result.returncode}: {detail}"
                )

            candidates = sorted(target_dir.glob("*.dxf"))
            if len(candidates) != 1:
                raise DWGProviderError(
                    "DWG conversion did not produce exactly one DXF artifact"
                )

            # Validate the generated artifact with the existing real DXF engine
            # before exposing it to the takeoff pipeline.
            read_dxf(candidates[0])
            verified = Path(tempfile.mkstemp(prefix="structuralpro-dwg-", suffix=".dxf")[1])
            verified.write_bytes(candidates[0].read_bytes())
            return verified

    def read(self, source: str | Path) -> DXFDocumentEvidence:
        converted = self.convert(source)
        try:
            return read_dxf(converted)
        finally:
            converted.unlink(missing_ok=True)
