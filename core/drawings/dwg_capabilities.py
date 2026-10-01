"""DWG capability detection and transparent backend diagnostics."""
from __future__ import annotations
from dataclasses import dataclass
import os, shutil
from pathlib import Path

@dataclass(frozen=True)
class DWGCapabilities:
    native_reader: bool
    converter: str|None
    converter_kind: str|None
    message: str

def detect_dwg_capabilities() -> DWGCapabilities:
    env=os.getenv("STRUCTURALPRO_DWG_CONVERTER")
    candidates=[env, shutil.which("ODAFileConverter"), shutil.which("dwg2dxf"), shutil.which("TeighaFileConverter")]
    converter=next((x for x in candidates if x),None)
    try:
        import libredwg  # type: ignore
        native=True
    except Exception:
        native=False
    kind=None
    if converter:
        name=Path(converter).name.lower()
        kind="oda" if "oda" in name else ("teigha" if "teigha" in name else "generic")
    if native: msg="خواندن مستقیم DWG با backend بومی فعال است."
    elif converter: msg=f"خواندن DWG با مبدل آفلاین {kind} و تحلیل DXF خروجی انجام می‌شود."
    else: msg="DWG نیازمند ODAFileConverter یا backend بومی است؛ DXF بدون مبدل قابل استفاده است."
    return DWGCapabilities(native,converter,kind,msg)
