from core.estimate.official_pricebook_sources_v1 import *

def test_registry():
    assert validate_sources() and len(registry_fingerprint())==64

def test_recent_year_coverage():
    assert coverage()["years"] == [1399,1400,1401,1402,1403,1404]

def test_direct_official_pages():
    assert any(x.year==1401 and "mdid=5681" in x.official_url for x in SOURCES)
    assert any(x.year==1403 and "mdid=5852" in x.official_url for x in SOURCES)
    assert any(x.year==1404 and "mdid=5957" in x.official_url for x in SOURCES)
