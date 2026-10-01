"""Project-management domain: schedule, progress, daily reports, resources, materials and meetings."""
from __future__ import annotations
from dataclasses import dataclass, asdict
import math
from typing import Any, Iterable

def _nonneg(v,label):
    v=float(v)
    if not math.isfinite(v) or v<0: raise ValueError(f"{label} must be finite and non-negative")
    return v
def _pct(v,label):
    v=float(v)
    if not math.isfinite(v) or not 0<=v<=100: raise ValueError(f"{label} must be between 0 and 100")
    return v

@dataclass(frozen=True)
class ScheduleTask:
    id:str; title:str; planned_start:str; planned_end:str; actual_start:str=""; actual_end:str=""; progress:float=0.0
@dataclass(frozen=True)
class DailyReport:
    id:str; date:str; summary:str; progress:float=0.0; weather:str=""; notes:str=""
@dataclass(frozen=True)
class ResourceRecord:
    id:str; name:str; kind:str; quantity:float; unit:str=""; date:str=""
@dataclass(frozen=True)
class MaterialRecord:
    id:str; name:str; quantity:float; unit:str; date:str=""; supplier:str=""
@dataclass(frozen=True)
class MeetingRecord:
    id:str; date:str; title:str; participants:str=""; decisions:str=""; actions:str=""

class ProjectManagement:
    def __init__(self,*,tasks:Iterable[ScheduleTask]=(),daily_reports:Iterable[DailyReport]=(),
                 resources:Iterable[ResourceRecord]=(),materials:Iterable[MaterialRecord]=(),
                 meetings:Iterable[MeetingRecord]=()):
        self.tasks=list(tasks); self.daily_reports=list(daily_reports); self.resources=list(resources)
        self.materials=list(materials); self.meetings=list(meetings); self.validate()

    def _ids(self,items,label):
        seen=set()
        for x in items:
            if not str(x.id).strip(): raise ValueError(f"{label} id is required")
            if x.id in seen: raise ValueError(f"duplicate {label} id: {x.id}")
            seen.add(x.id)
    def validate(self):
        for items,label in ((self.tasks,"task"),(self.daily_reports,"daily report"),(self.resources,"resource"),(self.materials,"material"),(self.meetings,"meeting")): self._ids(items,label)
        for x in self.tasks:
            if not x.title.strip(): raise ValueError("task title is required")
            _pct(x.progress,"task progress")
        for x in self.daily_reports: _pct(x.progress,"daily report progress")
        for x in self.resources: _nonneg(x.quantity,"resource quantity")
        for x in self.materials: _nonneg(x.quantity,"material quantity")
        return self

    def _add(self,target,item,label):
        if any(x.id==item.id for x in target): raise ValueError(f"duplicate {label} id")
        target.append(item)
        try: self.validate()
        except Exception: target.pop(); raise
        return item

    def add_task(self,x): return self._add(self.tasks,x,"task")
    def add_daily_report(self,x): return self._add(self.daily_reports,x,"daily report")
    def add_resource(self,x): return self._add(self.resources,x,"resource")
    def add_material(self,x): return self._add(self.materials,x,"material")
    def add_meeting(self,x): return self._add(self.meetings,x,"meeting")

    def schedule_summary(self):
        total=len(self.tasks); avg=sum(x.progress for x in self.tasks)/total if total else 0
        completed=sum(x.progress>=100 for x in self.tasks)
        return {"task_count":total,"completed_tasks":completed,"average_progress":avg}

    def actual_vs_plan(self):
        rows=[]
        for x in self.tasks:
            rows.append({**asdict(x),"started":bool(x.actual_start),"finished":bool(x.actual_end),
                         "delay":bool(x.actual_end and x.planned_end and x.actual_end>x.planned_end)})
        return rows

    def dashboard(self):
        schedule=self.schedule_summary()
        return {**schedule,"daily_report_count":len(self.daily_reports),"resource_count":len(self.resources),
                "material_record_count":len(self.materials),"meeting_count":len(self.meetings),
                "latest_report_date":max((x.date for x in self.daily_reports),default=""),
                "latest_material_date":max((x.date for x in self.materials),default="")}

    def export_dict(self)->dict[str,list[dict[str,Any]]]:
        return {k:[asdict(x) for x in getattr(self,k)] for k in
                ("tasks","daily_reports","resources","materials","meetings")}
