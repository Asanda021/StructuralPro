from __future__ import annotations
import hashlib,json,re,sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs,urljoin,urlparse,urlunparse
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from core.estimate.pricebook_row_extraction_v2 import extract_xlsx
ARCHIVE_INDEX="https://fehrestbaha.github.io/"
OFFICIAL_INDEX="https://acco.ir/فهرست-بها"
YEARS=range(1399,1405)
DISCIPLINES=("ابنیه","تاسیسات مکانیکی","تاسیسات برقی","مرمت بناهای تاریخی")

def norm_text(v):
    return re.sub(r"\s+"," ",v.replace("ي","ی").replace("ك","ک").replace("\u200c"," ")).strip()

class Parser(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows=[]; self.row=False; self.text=[]; self.href=None; self.ltxt=[]; self.links=[]
    def handle_starttag(self,t,a):
        a=dict(a)
        if t=="tr": self.row=True; self.text=[]; self.links=[]
        elif self.row and t=="a": self.href=a.get("href"); self.ltxt=[]
    def handle_data(self,d):
        if self.row:
            self.text.append(d)
            if self.href is not None: self.ltxt.append(d)
    def handle_endtag(self,t):
        if t=="a" and self.href is not None:
            self.links.append((" ".join(self.ltxt),self.href)); self.href=None; self.ltxt=[]
        elif t=="tr" and self.row:
            self.rows.append((norm_text(" ".join(self.text)),list(self.links))); self.row=False

def get(url):
    req=Request(url,headers={"User-Agent":"StructuralPro-PricebookSync/5.0","Accept":"*/*"})
    with urlopen(req,timeout=120) as r: return r.read(),r.headers.get("Content-Type","")

def rows(url):
    p=Parser(); body,_=get(url); p.feed(body.decode("utf-8","ignore")); return p.rows

def find_page(all_rows,y,d):
    needles=(norm_text(f"فهرست بهای واحد پایه رشته {d} سال {y}"),norm_text(f"فهرست بها {d} سال {y}"))
    for needle in needles:
        for txt,links in all_rows:
            if needle in txt and links: return urljoin(ARCHIVE_INDEX,links[0][1])
    return None

def links(page):
    p=Parser(); body,_=get(page); p.feed(body.decode("utf-8","ignore")); out=[]
    for _,ls in p.rows:
        for txt,href in ls:
            if not href: continue
            low=norm_text(f"{txt} {href}").lower()
            direct_ext=href.lower().split("?")[0].endswith((".xlsx",".xls"))
            download_host=any(h in href.lower() for h in ("drive.google.com","drive.usercontent.google.com","1drv.ms","onedrive.live.com"))
            labeled_download=any(k in low for k in ("excel","اکسل","download","دانلود"))
            if direct_ext or download_host or labeled_download:
                out.append(urljoin(page,href))
    return list(dict.fromkeys(out))

def google_drive_variants(url):
    u=urlparse(url)
    q=parse_qs(u.query)
    file_id=(q.get("id") or [None])[0]
    if not file_id: return [url]
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
            # XLSX is a ZIP container and starts with PK; HTML is never accepted.
            if len(data)<1024 or b"<html" in head or b"<!doctype" in head or b"<title" in head:
                raise RuntimeError("non-file response")
            dst.parent.mkdir(parents=True,exist_ok=True); dst.write_bytes(data)
            return hashlib.sha256(data).hexdigest(),len(data),ctype,candidate
        except Exception as exc:
            last=exc
    raise RuntimeError(f"download failed: {last}")

def slug(v):
    return re.sub(r"[^a-z0-9]+","_",v.lower()).strip("_") or "pricebook"

def main():
    root=ROOT; raw=root/"data/pricebooks/raw"; norm=root/"data/pricebooks/normalized"
    (root/"data/pricebooks").mkdir(parents=True,exist_ok=True)
    all_rows=rows(ARCHIVE_INDEX)
    manifest={"index":ARCHIVE_INDEX,"official_index":OFFICIAL_INDEX,"cells":[]}; failures=[]
    for y in YEARS:
      for d in DISCIPLINES:
       try:
        page=find_page(all_rows,y,d)
        if not page: raise RuntimeError("archive discovery failed")
        candidates=links(page); parsed=None
        for url in candidates:
            try:
                dst=raw/str(y)/(slug(d)+".xlsx")
                digest,size,ctype,used_url=download(url,dst)
                extracted=extract_xlsx(dst,y,d)
                if extracted:
                    parsed=(used_url,digest,size,dst,extracted); break
            except Exception:
                continue
        if parsed is None:
            raise RuntimeError(f"no parseable XLSX among {len(candidates)} candidates")
        url,digest,size,dst,extracted=parsed
        out=norm/str(y)/(slug(d)+".jsonl"); out.parent.mkdir(parents=True,exist_ok=True)
        with out.open("w",encoding="utf-8") as f:
            for x in extracted:
                f.write(json.dumps({
                    "year":x.year,"discipline":x.discipline,"item_code":x.item_code,
                    "description":x.description,"unit":x.unit,"unit_price":x.unit_price,
                    "source_sha256":x.source_sha256,"source_file":x.source_file,
                    "source_sheet":x.source_sheet
                },ensure_ascii=False)+"\n")
        manifest["cells"].append({
            "year":y,"discipline":d,"source_tier":"archive","archive_page":page,
            "download_url":url,"local_file":str(dst.relative_to(root)),
            "normalized_file":str(out.relative_to(root)),"sha256":digest,
            "bytes":size,"rows":len(extracted),
            "priced_rows":sum(x.unit_price is not None for x in extracted)
        })
        print(f"OK {y} {d}: {len(extracted)} rows")
       except Exception as e:
        failures.append({"year":y,"discipline":d,"error":str(e)})
        print(f"FAIL {y} {d}: {e}",file=sys.stderr)
    (root/"data/pricebooks/manifest.json").write_text(
        json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if failures:
        (root/"data/pricebooks/failures.json").write_text(
            json.dumps(failures,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        raise SystemExit(f"{len(failures)}/24 pricebook cells failed")
    print("ALL 24 PRICEBOOK CELLS EXTRACTED")

if __name__=="__main__":
    main()
