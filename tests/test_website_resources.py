from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "website" / "resources.html"
DATA = ROOT / "website" / "data" / "resources.json"


def test_resources_catalog_is_structured_and_bilingual():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert len(data["items"]) >= 10
    assert all(item["title"].get("en") and item["title"].get("fa") for item in data["items"])
    assert all(item["description"].get("en") and item["description"].get("fa") for item in data["items"])
    assert all(item["status"] in {"Available", "Planned", "Integration"} for item in data["items"])


def test_available_resources_point_to_existing_repository_docs():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    for item in data["items"]:
        if item["status"] != "Available" or not item["href"]:
            continue
        target = (PAGE.parent / item["href"]).resolve()
        assert target.exists(), f"Missing resource target: {item['id']} -> {item['href']}"


def test_resources_page_has_real_rtl_switch_and_structured_data_source():
    html = PAGE.read_text(encoding="utf-8")
    assert 'lang="en" dir="ltr"' in html
    assert 'get("lang")==="fa"' in html
    assert 'resources.html?lang=fa' in html
    assert 'data/resources.json' in html
    assert "[dir=rtl]" in html
    assert "Available" in html
    assert "Planned" in html


def test_resources_page_has_no_fake_social_proof_or_certification_claims():
    html = PAGE.read_text(encoding="utf-8").lower()
    banned = ["trusted by", "certified by", "award-winning", "number one", "best in class"]
    assert not any(term in html for term in banned)
