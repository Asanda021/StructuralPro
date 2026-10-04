from core.estimate.official_pricebook_sources_v1 import *
def test_registry(): assert validate_sources() and len(registry_fingerprint())==64
def test_official_1404(): assert any(x.year==1404 and "sama.mporg.ir" in x.official_url for x in SOURCES)
