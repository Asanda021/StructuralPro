from __future__ import annotations
import hashlib
import json
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.estimate.pricebook_row_extraction_v2 import extract_xlsx

ARCHIVE_INDEX = "https://fehrestbaha.github.io/"
OFFICIAL_INDEX = "https://acco.ir/فهرست-بها"
YEARS = range(1399, 1405)
DISCIPLINES = ("ابنیه", "تاسیسات مکانیکی", "تاسیسات برقی", "مرمت بناهای تاریخی")

def norm_text(value: str) -> str:
    value = value.replace("ي", "ی").replace("ك", "ک").replace("\u200c", " ")
    return re.sub(r"\s+", " ", value).strip()

class ArchiveParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self._in_row = False
        self._row_text = []
        self._row_links = []
        self._href = None
        self._link_text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "tr":
            self._in_row = True
            self._row_text = []
            self._row_links = []
        elif self._in_row and tag == "a":
            self._href = attrs.get("href")
            self._link_text = []

    def handle_data(self, data):
        if not self._in_row:
            return
        if self._href is not None:
            self._link_text.append(data)
        self._row_text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            self._row_links.append((" ".join(self._link_text), self._href))
            self._href = None
            self._link_text = []
        elif tag == "tr" and self._in_row:
            self.rows.append((norm_text(" ".join(self._row_text)), list(self._row_links)))
            self._in_row = False

def get(url: str):
    req = Request(url, headers={"User-Agent": "StructuralPro-PricebookSync/2.0"})
    with urlopen(req, timeout=90) as response:
        return response.read(), response.headers.get("Content-Type", "")

def archive_rows(url: str):
    body, _ = get(url)
    parser = ArchiveParser()
    parser.feed(body.decode("utf-8", "ignore"))
    return parser.rows

def find_download_page(rows, year: int, discipline: str):
    wanted = norm_text(f"دانلود فایل اکسل فهرست بهای واحد پایه رشته {discipline} سال {year}")
    candidates = []
    for row_text, links in rows:
        if wanted in row_text:
            candidates.extend(urljoin(ARCHIVE_INDEX, href) for _, href in links if href)
    if not candidates:
        needle = norm_text(f"فهرست بهای واحد پایه رشته {discipline} سال {year}")
        for row_text, links in rows:
            if needle in row_text and links:
                candidates.extend(urljoin(ARCHIVE_INDEX, href) for _, href in links if href)
    if not candidates:
        raise RuntimeError(f"archive page not found: {wanted}")
    return candidates[0]

def find_excel(page_url: str):
    body, _ = get(page_url)
    parser = ArchiveParser()
    parser.feed(body.decode("utf-8", "ignore"))
    candidates = []
    for _, links in parser.rows:
        for text, href in links:
            low = norm_text(f"{text} {href}").lower()
            if href.lower().endswith((".xlsx", ".xls", ".zip", ".rar")) or "excel" in low or "اکسل" in low or "drive.google.com" in href.lower() or "download" in low:
                candidates.append(urljoin(page_url, href))
    if not candidates:
        raise RuntimeError(f"excel/download link not found: {page_url}")
    return candidates[-1]

def download(url: str, dst: Path):
    data, ctype = get(url)
    if not data or len(data) < 1024:
        raise RuntimeError(f"empty/suspicious download: {url}")
    sample = data[:1024].lower()
    if b"<html" in sample or b"<!doctype" in sample:
        raise RuntimeError(f"HTML returned instead of file: {url}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(data)
    return hashlib.sha256(data).hexdigest(), len(data), ctype

def slug(value: str):
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "pricebook"

def main():
    root = ROOT
    raw = root / "data/pricebooks/raw"
    norm = root / "data/pricebooks/normalized"
    (root / "data/pricebooks").mkdir(parents=True, exist_ok=True)
    rows = archive_rows(ARCHIVE_INDEX)
    manifest = {"index": ARCHIVE_INDEX, "official_index": OFFICIAL_INDEX, "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "cells": []}
    failures = []
    for year in YEARS:
        for discipline in DISCIPLINES:
            try:
                page = find_download_page(rows, year, discipline)
                file_url = find_excel(page)
                dst = raw / str(year) / (slug(discipline) + ".xlsx")
                digest, size, _ = download(file_url, dst)
                extracted = extract_xlsx(dst, year, discipline)
                if not extracted:
                    raise RuntimeError("zero extracted rows")
                out = norm / str(year) / (slug(discipline) + ".jsonl")
                out.parent.mkdir(parents=True, exist_ok=True)
                with out.open("w", encoding="utf-8") as fh:
                    for item in extracted:
                        fh.write(json.dumps({"year": item.year, "discipline": item.discipline, "item_code": item.item_code, "description": item.description, "unit": item.unit, "unit_price": item.unit_price, "source_sha256": item.source_sha256, "source_file": item.source_file, "source_sheet": item.source_sheet}, ensure_ascii=False) + "\n")
                manifest["cells"].append({"year": year, "discipline": discipline, "source_tier": "archive", "archive_page": page, "download_url": file_url, "local_file": str(dst.relative_to(root)), "normalized_file": str(out.relative_to(root)), "sha256": digest, "bytes": size, "rows": len(extracted), "priced_rows": sum(item.unit_price is not None for item in extracted)})
                print(f"OK {year} {discipline}: {len(extracted)} rows")
            except Exception as exc:
                failures.append({"year": year, "discipline": discipline, "error": str(exc)})
                print(f"FAIL {year} {discipline}: {exc}", file=sys.stderr)
    manifest_path = root / "data/pricebooks/manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if failures:
        (root / "data/pricebooks/failures.json").write_text(json.dumps(failures, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise SystemExit(f"{len(failures)}/24 pricebook cells failed")
    failure_file = root / "data/pricebooks/failures.json"
    if failure_file.exists():
        failure_file.unlink()
    print("ALL 24 PRICEBOOK CELLS EXTRACTED")

if __name__ == "__main__":
    main()
