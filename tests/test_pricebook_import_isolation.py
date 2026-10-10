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
