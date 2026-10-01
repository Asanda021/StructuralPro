from core.pricing.catalog import PriceCatalog, PriceItem
from core.takeoff.boq import build_boq, boq_summary
from core.takeoff.costing import cost_breakdown

def test_price_catalog_year_group_chapter_search_and_snapshot():
    c=PriceCatalog([PriceItem(1405,"ابنیه","بتن","A-1","بتن آماده","m3",1200000)])
    assert c.years()==[1405]
    assert c.groups(1405)==["ابنیه"]
    assert c.chapters(1405,"ابنیه")==["بتن"]
    assert c.search("بتن",1405)[0].code=="A-1"
    assert c.resolve("A-1",1405,"m3")["status"]=="ok"
    assert c.snapshot(["A-1"],1405)[0]["unit_price"]==1200000

def test_boq_aggregate_and_summary():
    rows=[
        {"source":"drawing","description":"Concrete","quantity":2,"unit":"m3","price_code":"A","unit_price":100},
        {"source":"drawing","description":"Concrete","quantity":3,"unit":"m3","price_code":"A","unit_price":100},
    ]
    boq=build_boq(rows)
    assert len(boq)==1 and boq[0]["quantity"]==5 and boq[0]["total"]==500
    assert boq_summary(boq)["grand_total"]==500

def test_costing_factors():
    out=cost_breakdown([{"group":"ابنیه","price_code":"A","quantity":2,"unit_price":100}],{"بالاسری":0.1})
    assert out["base"]==200 and out["grand_total"]==220
