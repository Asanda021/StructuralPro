"""Regression tests for fail-closed pricebook replacement and atomic import."""
import csv
import pytest

from core.pricing.catalog import PriceCatalog, PriceItem
from core.pricing.import_service import PricebookImportService


def _item(group, code, price=10):
    return PriceItem(1404, group, "01", code, "test", "m2", price)


def _write(path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["year", "group", "chapter", "code", "description", "unit", "unit_price"])
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(year=row.year, group=row.group, chapter=row.chapter, code=row.code,
                                 description=row.description, unit=row.unit, unit_price=row.unit_price))


def test_replace_one_discipline_keeps_other_discipline(tmp_path):
    catalog = PriceCatalog([_item("ابنیه", "100", 10), _item("برق", "200", 20)])
    path = tmp_path / "prices.csv"
    _write(path, [_item("ابنیه", "300", 30)])
    PricebookImportService(catalog).import_file(path, year=1404, replace_year=True)
    assert catalog.get("100", 1404) is None
    assert catalog.get("200", 1404).unit_price == 20
    assert catalog.get("300", 1404).unit_price == 30


def test_cross_discipline_code_collision_rejected_without_mutation(tmp_path):
    catalog = PriceCatalog([_item("برق", "100", 20)])
    path = tmp_path / "prices.csv"
    _write(path, [_item("ابنیه", "100", 30)])
    with pytest.raises(ValueError, match="کد یکسان"):
        PricebookImportService(catalog).import_file(path, year=1404, replace_year=True)
    assert catalog.get("100", 1404).group == "برق"
    assert catalog.get("100", 1404).unit_price == 20


def test_duplicate_import_codes_rejected_without_mutation(tmp_path):
    catalog = PriceCatalog([_item("برق", "200", 20)])
    path = tmp_path / "prices.csv"
    _write(path, [_item("ابنیه", "100", 30), _item("ابنیه", "100", 40)])
    with pytest.raises(ValueError, match="تکراری"):
        PricebookImportService(catalog).import_file(path, year=1404, replace_year=True)
    assert catalog.get("200", 1404).unit_price == 20
    assert catalog.get("100", 1404) is None


def test_custom_price_conflict_rejected_without_losing_override(tmp_path):
    catalog = PriceCatalog([_item("ابنیه", "100", 10)])
    catalog.set_custom_price("100", 1404, 77, reason="approved by user")
    path = tmp_path / "prices.csv"
    _write(path, [_item("ابنیه", "100", 30)])
    with pytest.raises(ValueError, match="قیمت سفارشی"):
        PricebookImportService(catalog).import_file(path, year=1404, replace_year=True)
    assert catalog.get("100", 1404).unit_price == 77
    assert catalog._items[(1404, "100")].unit_price == 10


def test_unrelated_custom_price_survives_other_discipline_import(tmp_path):
    catalog = PriceCatalog([_item("برق", "200", 20)])
    catalog.set_custom_price("200", 1404, 55)
    path = tmp_path / "prices.csv"
    _write(path, [_item("ابنیه", "100", 30)])
    PricebookImportService(catalog).import_file(path, year=1404, replace_year=True)
    assert catalog.get("200", 1404).unit_price == 55
    assert catalog.get("100", 1404).unit_price == 30


def test_import_preserves_existing_price_history(tmp_path):
    catalog = PriceCatalog([_item("ابنیه", "100", 10)])
    catalog.add(_item("ابنیه", "100", 15))
    assert catalog.price_history("100", 1404)
    previous = catalog.price_history("100", 1404)
    path = tmp_path / "prices.csv"
    _write(path, [_item("ابنیه", "100", 30)])
    PricebookImportService(catalog).import_file(path, year=1404, replace_year=True)
    history = catalog.price_history("100", 1404)
    assert history[:len(previous)] == previous
    assert history[-1] == {
        "year": 1404, "code": "100", "old_price": 15, "new_price": 30,
    }


def test_direct_csv_import_does_not_delete_other_discipline():
    catalog = PriceCatalog([_item("برق", "200", 20), _item("ابنیه", "100", 10)])
    csv_text = PriceCatalog([_item("ابنیه", "300", 30)]).export_csv()
    assert catalog.import_csv(csv_text, replace_year=True) == 1
    assert catalog.get("200", 1404).unit_price == 20
    assert catalog.get("100", 1404) is None
    assert catalog.get("300", 1404).unit_price == 30


def test_direct_csv_import_rejects_conflicting_override_atomically():
    catalog = PriceCatalog([_item("ابنیه", "100", 10)])
    catalog.set_custom_price("100", 1404, 77)
    csv_text = PriceCatalog([_item("ابنیه", "100", 30)]).export_csv()
    with pytest.raises(ValueError, match="custom prices"):
        catalog.import_csv(csv_text, replace_year=True)
    assert catalog.get("100", 1404).unit_price == 77
    assert catalog._items[(1404, "100")].unit_price == 10


def test_service_import_appends_price_change_to_audit_history(tmp_path):
    catalog = PriceCatalog([_item("ابنیه", "100", 10)])
    path = tmp_path / "prices.csv"
    _write(path, [_item("ابنیه", "100", 30)])
    PricebookImportService(catalog).import_file(path, year=1404, replace_year=True)
    assert catalog.price_history("100", 1404)[-1] == {
        "year": 1404, "code": "100", "old_price": 10, "new_price": 30,
    }
