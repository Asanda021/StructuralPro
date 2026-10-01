from core.takeoff.engine import TakeoffEngine
from core.pricing.catalog import PriceCatalog, PriceItem
from core.pricing.registry import DatasetInfo, PriceDatasetRegistry
from core.pricing.validation import normalize_code, validate_price_rows
from core.takeoff.price_mapping import PriceMapper, units_compatible

def test_unified_takeoff_batch_and_summary():
    e = TakeoffEngine()
    rows = e.batch([
        {"domain":"building","item":"wall","length":5,"height":3,"openings":2},
        {"domain":"mechanical","item":"pipe","length":12},
        {"domain":"electrical","item":"cable","length":10,"count":2},
        {"domain":"civil","item":"excavation","length":4,"width":2,"depth":1},
    ])
    assert [r.unit for r in rows] == ["m2","m","m","m3"]
    assert e.summarize(rows)["row_count"] == 4

def test_price_dataset_registry():
    r = PriceDatasetRegistry()
    r.register(DatasetInfo(1404,"ابنیه","فهرست بهای ابنیه 1404","سازمان برنامه و بودجه",True,"1404"))
    assert r.get(1404,"ابنیه").verified is True
    assert r.years() == [1404]

def test_price_row_validation_and_persian_digits():
    assert normalize_code("۰۱-۲۳") == "01-23"
    errors = validate_price_rows([{"code":"۰۱.۰۲","description":"بتن","unit":"m3","unit_price":1200}])
    assert errors == []

def test_price_mapping_exact_and_ambiguous():
    c = PriceCatalog([
        PriceItem(1404,"ابنیه","بتن","0101","بتن مگر","m3",100),
        PriceItem(1404,"ابنیه","بتن","0102","بتن سازه‌ای","m3",200),
    ])
    m = PriceMapper(c)
    exact = m.map_row({"description":"بتن","unit":"m3","price_code":"0101","quantity":3},1404)
    assert exact["status"] == "exact"
    assert units_compatible("مترمکعب","m3") is True
