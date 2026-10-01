"""Configurable report layout independent of report rendering backend."""
from dataclasses import dataclass,field
_FIELD_MAP={"ردیف":"item_no","کد":"price_code","شرح":"description","مقدار":"quantity","واحد":"unit","بهای واحد":"unit_price","مبلغ":"total"}
@dataclass
class ReportLayout:
    title:str="گزارش متره و برآورد"
    columns:list[str]=field(default_factory=lambda:["ردیف","کد","شرح","مقدار","واحد","بهای واحد","مبلغ"])
    group_by:str=""
    rtl:bool=True
    def visible(self,row):
        out={label:row.get(_FIELD_MAP.get(label,label),row.get(label,"")) for label in self.columns}
        for key in ("item_no","price_code","description","quantity","unit","unit_price","total"):
            out.setdefault(key,row.get(key,""))
        return out
    def reorder(self,columns):
        self.columns=list(columns)
        return self
