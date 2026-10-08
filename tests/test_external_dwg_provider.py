from pathlib import Path

import pytest

from core.cad.external_dwg_provider_v1 import (
    DWGConverterConfig,
    DWGProviderError,
    ExternalDWGConverterProvider,
)


def test_dwg_provider_fails_closed_when_converter_is_missing(tmp_path: Path) -> None:
    source = tmp_path / "plan.dwg"
    source.write_bytes(b"DWG-test")
    provider = ExternalDWGConverterProvider(
        DWGConverterConfig(executable=str(tmp_path / "missing-converter.exe"))
    )

    with pytest.raises(DWGProviderError, match="converter was not found"):
        provider.read(source)


def test_dwg_provider_rejects_non_dwg_input(tmp_path: Path) -> None:
    source = tmp_path / "plan.dxf"
    source.write_text("0\nSECTION\n2\nHEADER\n0\nENDSEC\n0\nEOF\n", encoding="utf-8")
    provider = ExternalDWGConverterProvider(
        DWGConverterConfig(executable="missing-converter")
    )

    with pytest.raises(DWGProviderError, match="accepts .dwg only"):
        provider.convert(source)


def test_dwg_provider_command_is_explicit() -> None:
    provider = ExternalDWGConverterProvider(
        DWGConverterConfig(executable="ODAFileConverter.exe")
    )
    command = provider._command(
        "ODAFileConverter.exe",
        Path("C:/input"),
        Path("C:/output"),
    )

    assert command == (
        "ODAFileConverter.exe",
        "C:/input",
        "C:/output",
        "ACAD2018",
        "DXF",
        "0",
        "1",
        "*.DWG",
    )
