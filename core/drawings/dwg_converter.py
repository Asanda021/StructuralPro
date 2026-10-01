"""Offline DWG conversion boundary with deterministic executable discovery and validation."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os, shutil, subprocess, tempfile
from core.drawings.dwg_capabilities import detect_dwg_capabilities

@dataclass(frozen=True)
class ConverterResult:
    source: Path
    output: Path
    converter: str

class OfflineDWGConverter:
    def __init__(self, executable: str|None=None):
        self.executable=executable or os.getenv("STRUCTURALPRO_DWG_CONVERTER") or shutil.which("dwg2dxf") or shutil.which("ODAFileConverter")

    @property
    def available(self)->bool:
        return bool(self.executable)

    @property
    def capabilities(self):
        return detect_dwg_capabilities()

    def convert(self, source: str|Path, output_dir: str|Path|None=None)->ConverterResult:
        src=Path(source)
        if not src.exists(): raise FileNotFoundError(src)
        if src.suffix.lower()!=".dwg": raise ValueError("source must be .dwg")
        if not self.executable:
            raise RuntimeError("No offline DWG converter installed. Install ODAFileConverter or configure STRUCTURALPRO_DWG_CONVERTER.")
        out=Path(output_dir or tempfile.mkdtemp(prefix="structuralpro_dwg_")); out.mkdir(parents=True,exist_ok=True)
        target=out/(src.stem+".dxf")
        name=Path(self.executable).name.lower()
        if "odafileconverter" in name:
            odir=out/"oda"; odir.mkdir(exist_ok=True)
            proc=subprocess.run([self.executable,str(src.parent),str(odir),"ACAD2018","DXF","0","1",src.name],capture_output=True,text=True)
            if proc.returncode: raise RuntimeError(proc.stderr or "ODA conversion failed")
            matches=list(odir.glob("*.dxf"))
            if matches: target=matches[0]
        else:
            proc=subprocess.run([self.executable,str(src),str(target)],capture_output=True,text=True)
            if proc.returncode: raise RuntimeError(proc.stderr or "DWG conversion failed")
        if not target.exists() or target.stat().st_size==0: raise RuntimeError("converter produced no DXF")
        return ConverterResult(src,target,str(self.executable))
