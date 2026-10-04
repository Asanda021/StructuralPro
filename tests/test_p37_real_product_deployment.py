"""P37 production deployment contract tests."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_p37_deployment_contract_is_complete():
    workflow = ROOT / ".github" / "workflows" / "p37-real-product-deployment.yml"
    doc = ROOT / "docs" / "P37_REAL_PRODUCT_DEPLOYMENT.md"
    assert workflow.exists()
    assert doc.exists()
    text = workflow.read_text(encoding="utf-8")
    for marker in (
        'tags: ["v*"]', "actions/checkout@v4", "actions/setup-python@v5",
        "packaging/build_windows.ps1", "packaging/windows_installer_smoke.ps1",
        "packaging/generate_sha256.ps1", "packaging/generate_release_manifest.ps1",
        "actions/upload-artifact@v4", "softprops/action-gh-release@v2",
    ):
        assert marker in text, marker

def test_p37_is_desktop_first_and_does_not_fake_cloud_deployment():
    text = (ROOT / "docs" / "P37_REAL_PRODUCT_DEPLOYMENT.md").read_text(encoding="utf-8")
    assert "Windows desktop" in text
    assert "GitHub Release" in text
    assert "cloud-hosted" in text
    assert "not" in text.lower()
