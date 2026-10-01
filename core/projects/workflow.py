"""Project library, packages, backups, audit and readiness checks."""
from __future__ import annotations
import json, zipfile
from pathlib import Path
from datetime import datetime

def project_health(project):
    issues=[]
    if not str(project.get("name","")).strip(): issues.append("missing_name")
    if not project.get("takeoffs"): issues.append("no_takeoffs")
    for i,row in enumerate(project.get("takeoffs",[]) or [],1):
        if not row.get("member_code"): issues.append(f"takeoff_{i}_missing_member_code")
        if not row.get("quantities"): issues.append(f"takeoff_{i}_missing_quantities")
    return {"ready":not issues,"issues":issues}

def audit_project(project):
    return {"project_id":project.get("id"),"name":project.get("name",""),"takeoff_count":len(project.get("takeoffs",[]) or []),"checked_at":datetime.now().isoformat(timespec="seconds"),"health":project_health(project)}

def save_template(project,path):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(project,ensure_ascii=False,indent=2),encoding="utf-8"); return path

def load_template(path): return json.loads(Path(path).read_text(encoding="utf-8"))

def export_package(project,path,attachments=()):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(path,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("project.json",json.dumps(project,ensure_ascii=False,indent=2))
        z.writestr("audit.json",json.dumps(audit_project(project),ensure_ascii=False,indent=2))
        for item in attachments:
            p=Path(item)
            if p.exists(): z.write(p,f"attachments/{p.name}")
    return path

def import_package(path):
    with zipfile.ZipFile(path) as z: return json.loads(z.read("project.json").decode("utf-8"))

def backup_project(project,path): return export_package(project,path)

def copy_project(project,new_id=None):
    out=json.loads(json.dumps(project,ensure_ascii=False));
    if new_id: out["id"]=new_id
    out["copied_from"]=project.get("id"); return out
