from core.estimate.pricebook_historical_matrix_v1 import required_cells,validate_cells
from core.estimate.pricebook_full_building_pricing_v2 import price_full_building
def test_p100_requires_all_24_cells():
    cells=[{"year":y,"discipline":d,"source_url":"https://official.example/x","local_path":f"{y}-{i}.xlsx","sha256":"a"*64,"row_count":1} for i,(y,d) in enumerate(required_cells())]
    assert validate_cells(cells)["cells"]==24
def test_p101_prices_full_building_shape():
    class R:
        year=1404; discipline="ابنیه"; item_code="080101"; description="بتن"; unit="م3"; unit_price=1250000; source_sha256="b"*64; source_file="1404.xlsx"
    out=price_full_building([{"takeoff_id":"q1","item_code":"۰۸۰۱۰۱","unit":"م3","quantity":3.5}],[R()],1404,"ابنیه")
    assert out[0]["total"]==4375000 and out[0]["source_sha256"]=="b"*64
