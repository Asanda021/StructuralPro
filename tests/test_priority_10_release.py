from pathlib import Path

from core.platform.release import LicenseRecord, LicenseVerifier, ReleaseInfo, load_version

ROOT=Path(__file__).resolve().parents[1]

def test_version_is_canonical():
    version=load_version()
    assert version=="0.1.0"
    assert len(version.split("."))==3

def test_release_metadata_is_serializable():
    info=ReleaseInfo("StructuralPro",load_version(),"stable")
    assert info.as_dict()=={"name":"StructuralPro","version":"0.1.0","channel":"stable"}

def test_license_payload_is_deterministic_and_verifiable():
    record=LicenseRecord("StructuralPro","LIC-001","Demo",features=("takeoff","reports"))
    seen={}
    def verifier(payload,signature):
        seen["payload"]=payload
        seen["signature"]=signature
        return signature=="valid"
    service=LicenseVerifier(verifier)
    assert service.verify(record,"valid")
    assert not service.verify(record,"invalid")
    assert seen["payload"]==record.canonical_bytes()

def test_release_surfaces_exist():
    assert (ROOT/"packaging/build_windows.ps1").exists()
    assert (ROOT/"packaging/structuralpro.spec").exists()
    assert (ROOT/"packaging/installer.iss").exists()
    assert (ROOT/".github/workflows/windows-release.yml").exists()

def test_installer_tracks_canonical_version():
    text=(ROOT/"packaging/installer.iss").read_text(encoding="utf-8")
    assert '#define MyAppVersion "0.1.0"' in text
