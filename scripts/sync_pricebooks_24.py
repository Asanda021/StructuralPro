from __future__ import annotations
import hashlib,json,re,sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs,urljoin,urlparse
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from core.estimate.pricebook_row_extraction_v2 import extract_xlsx

ARCHIVE_INDEX="https://fehrestbaha.github.io/"
OFFICIAL_INDEX="https://acco.ir/فهرست-بها"
YEARS=range(1399,1405)
DISCIPLINES=("ابنیه","تاسیسات مکانیکی","تاسیسات برقی","مرمت بناهای تاریخی")
DISCIPLINE_SLUGS={
    "ابنیه":"abnieh",
    "تاسیسات مکانیکی":"mechanic",
    "تاسیسات برقی":"barghi",
    "مرمت بناهای تاریخی":"maremat",
}

def norm_text(v):
    return re.sub(r"\s+"," ",v.replace("ي","ی").replace("ك","ک").replace("\u200c"," ")).strip()

class AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
        self.href=None
        self.text=[]
    def handle_starttag(self,t,a):
        if t=="a":
            self.href=dict(a).get("href")
            self.text=[]
    def handle_data(self,d):
        if self.href is not None:
            self.text.append(d)
    def handle_endtag(self,t):
        if t=="a" and self.href is not None:
            self.links.append((norm_text(" ".join(self.text)),self.href))
            self.href=None
            self.text=[]

def get(url):
    req=Request(url,headers={"User-Agent":"StructuralPro-PricebookSync/7.0","Accept":"*/*"})
    with urlopen(req,timeout=120) as r:
        return r.read(),r.headers.get("Content-Type","")

def archive_page(y,d):
    slug=DISCIPLINE_SLUGS[d]
    return f"{ARCHIVE_INDEX}fehrest_baha_years/{slug}_{y}.html"

def links(page):
    p=AnchorParser()
    body,_=get(page)
    p.feed(body.decode("utf-8","ignore"))
    out=[]
    for txt,href in p.links:
        if not href:
            continue
        low=norm_text(f"{txt} {href}").lower()
        path=urlparse(href).path.lower()
        direct_ext=path.endswith((".xlsx",".xls"))
        download_host=any(h in href.lower() for h in (
            "drive.google.com","drive.usercontent.google.com","1drv.ms","onedrive.live.com"
        ))
        labeled_download=any(k in low for k in (
            "excel","xlsx","xls","اکسل","download","دانلود"
        ))
        if direct_ext or download_host or labeled_download:
            out.append(urljoin(page,href))
    return list(dict.fromkeys(out))

def google_drive_variants(url):
    u=urlparse(url)
    q=parse_qs(u.query)
    file_id=(q.get("id") or [None])[0]
    if not file_id:
        return [url]
    return list(dict.fromkeys([
        url,
        f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t",
        f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t",
    ]))

def download(url,dst):
    last=None
    for candidate in google_drive_variants(url):
        try:
            data,ctype=get(candidate)
            head=data[:4096].lower()
            if len(data)<1024 or b"<html" in head or b"<!doctype" in head or b"<title" in head:
                raise RuntimeError("non-file response")
            dst.parent.mkdir(parents=True,exist_ok=True)
            dst.write_bytes(data)
            return hashlib.sha256(data).hexdigest(),len(data),ctype,candidate
        except Exception as exc:
            last=exc
    raise RuntimeError(f"download failed: {last}")

def main():
    root=ROOT
    raw=root/"data/pricebooks/raw"
    norm=root/"data/pricebooks/normalized"
    (root/"data/pricebooks").mkdir(parents=True,exist_ok=True)
    manifest={"index":ARCHIVE_INDEX,"official_index":OFFICIAL_INDEX,"cells":[]}
    failures=[]

    for y in YEARS:
        for d in DISCIPLINES:
            try:
                page=archive_page(y,d)
                candidates=links(page)
                if not candidates:
                    raise RuntimeError(f"excel/download link not found: {page}")

                parsed=None
                file_slug=DISCIPLINE_SLUGS[d]
                for url in candidates:
                    try:
                        dst=raw/str(y)/(file_slug+".xlsx")
                        digest,size,ctype,used_url=download(url,dst)
                        extracted=extract_xlsx(dst,y,d)
                        if extracted:
                            parsed=(used_url,digest,size,dst,extracted)
                            break
                    except Exception:
                        continue

                if parsed is None:
                    raise RuntimeError(f"no parseable XLSX among {len(candidates)} candidates")

                url,digest,size,dst,extracted=parsed
                out=norm/str(y)/(file_slug+".jsonl")
                out.parent.mkdir(parents=True,exist_ok=True)
                with out.open("w",encoding="utf-8") as f:
                    for x in extracted:
                        f.write(json.dumps({
                            "year":x.year,
                            "discipline":x.discipline,
                            "item_code":x.item_code,
                            "description":x.description,
                            "unit":x.unit,
                            "unit_price":x.unit_price,
                            "source_sha256":x.source_sha256,
                            "source_file":x.source_file,
                            "source_sheet":x.source_sheet,
                        },ensure_ascii=False)+"\n")

                manifest["cells"].append({
                    "year":y,
                    "discipline":d,
                    "source_tier":"archive",
                    "archive_page":page,
                    "download_url":url,
                    "local_file":str(dst.relative_to(root)),
                    "normalized_file":str(out.relative_to(root)),
                    "sha256":digest,
                    "bytes":size,
                    "rows":len(extracted),
                    "priced_rows":sum(x.unit_price is not None for x in extracted),
                })
                print(f"OK {y} {d}: {len(extracted)} rows")
            except Exception as e:
                failures.append({"year":y,"discipline":d,"error":str(e)})
                print(f"FAIL {y} {d}: {e}",file=sys.stderr)

    (root/"data/pricebooks/manifest.json").write_text(
        json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    if failures:
        (root/"data/pricebooks/failures.json").write_text(
            json.dumps(failures,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
        )
        raise SystemExit(f"{len(failures)}/24 pricebook cells failed")
    print("ALL 24 PRICEBOOK CELLS EXTRACTED")

if __name__=="__main__":
    main()
