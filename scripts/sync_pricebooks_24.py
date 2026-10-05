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

from core.estimate.pricebook_row_extraction_v2 import extract_xlsx

ARCHIVE_INDEX = "https://fehrestbaha.github.io/"
OFFICIAL_INDEX = "https://acco.ir/فهرست-بها"
YEARS = range(1399, 1405)
DISCIPLINES = ("ابنیه", "تاسیسات مکانیکی", "تاسیسات برقی", "مرمت بناهای تاریخی")
TITLE_PREFIX = "دانلود فایل اکسل فهرست بهای واحد پایه رشته "

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
        self.href=None
        self.text=[]
    def handle_starttag(self, tag, attrs):
        if tag=="a":
            self.href=dict(attrs).get("href")
            self.text=[]
    def handle_data(self, data):
        if self.href is not None:
            self.text.append(data)
    def handle_endtag(self, tag):
        if tag=="a" and self.href is not None:
            self.links.append((" ".join("".join(self.text).split()), self.href))
            self.href=None
            self.text=[]

def get(url):
    req=Request(url,headers={"User-Agent":"StructuralPro-PricebookSync/1.0"})
    with urlopen(req,timeout=90) as r:
        return r.read(), r.headers.get("Content-Type","")

def links_from(url):
    body,_=get(url)
    p=Links(); p.feed(body.decode("utf-8","ignore"))
    return [(t,urljoin(url,h)) for t,h in p.links if h]

def find_download_page(index_links,title):
    candidates=[(t,h) for t,h in index_links if title in t]
    if not candidates:
        raise RuntimeError(f"archive page not found: {title}")
    return candidates[0][1]

def find_excel(page_url):
    links=links_from(page_url)
    preferred=[]
    for text,href in links:
        low=(text+" "+href).lower()
        if "excel" in low or href.lower().endswith((".xlsx",".xls")) or "drive.google.com" in low:
            preferred.append(href)
    if not preferred:
        raise RuntimeError(f"excel download link not found: {page_url}")
    return preferred[-1]

def download(url,dst):
    data,ctype=get(url)
    if not data or len(data)<1024:
        raise RuntimeError(f"empty/suspicious download: {url}")
    sample=data[:512].lower()
    if b"<html" in sample or b"<!doctype" in sample:
        raise RuntimeError(f"HTML returned instead of file: {url}")
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_bytes(data)
    return hashlib.sha256(data).hexdigest(), len(data), ctype

def slug(s):
    return re.sub(r"[^a-z0-9]+","_",s.lower()).strip("_")

def main():
    root=Path(__file__).resolve().parents[1]
    raw=root/"data/pricebooks/raw"
    norm=root/"data/pricebooks/normalized"
    index_links=links_from(ARCHIVE_INDEX)
    manifest={"index":ARCHIVE_INDEX,"official_index":OFFICIAL_INDEX,"generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"cells":[]}
    failures=[]
    for year in YEARS:
        for discipline in DISCIPLINES:
            title=f"{TITLE_PREFIX}{discipline} سال {year}"
            try:
                page=find_download_page(index_links,title)
                file_url=find_excel(page)
                dst=raw/str(year)/(slug(discipline)+".xlsx")
                digest,size,ctype=download(file_url,dst)
                rows=extract_xlsx(dst,year,discipline)
                if not rows:
                    raise RuntimeError("zero extracted rows")
                out=norm/str(year)/(slug(discipline)+".jsonl")
                out.parent.mkdir(parents=True,exist_ok=True)
                with out.open("w",encoding="utf-8") as fh:
                    for r in rows:
                        fh.write(json.dumps({
                            "year":r.year,"discipline":r.discipline,"item_code":r.item_code,
                            "description":r.description,"unit":r.unit,"unit_price":r.unit_price,
                            "source_sha256":r.source_sha256,"source_file":r.source_file,
                            "source_sheet":r.source_sheet
                        },ensure_ascii=False)+"\n")
                manifest["cells"].append({
                    "year":year,"discipline":discipline,"source_tier":"archive",
                    "archive_page":page,"download_url":file_url,
                    "local_file":str(dst.relative_to(root)),
                    "normalized_file":str(out.relative_to(root)),
                    "sha256":digest,"bytes":size,"rows":len(rows),
                    "priced_rows":sum(r.unit_price is not None for r in rows)
                })
                print(f"OK {year} {discipline}: {len(rows)} rows")
            except Exception as exc:
                failures.append({"year":year,"discipline":discipline,"error":str(exc)})
                print(f"FAIL {year} {discipline}: {exc}",file=sys.stderr)
    (root/"data/pricebooks/manifest.json").write_text(
        json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if failures:
        (root/"data/pricebooks/failures.json").write_text(
            json.dumps(failures,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        raise SystemExit(f"{len(failures)}/24 pricebook cells failed")
    f=root/"data/pricebooks/failures.json"
    if f.exists(): f.unlink()
    print("ALL 24 PRICEBOOK CELLS EXTRACTED")

if __name__=="__main__":
    main()
