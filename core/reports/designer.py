"""Configurable report layout independent of report rendering backend."""
from dataclasses import dataclass,field
@dataclass
class ReportLayout:
    title:str="گزارش متره و برآورد"; columns:list[str]=field(default_factory=lambda:["ردیف","کد","شرح","مقدار","واحد","بهای واحد","مبلغ"])
    group_by:str=""; rtl:bool=True
    def visible(self,row):
        return {k:row.get(k,"") for k in self.columns}
    def reorder(self,columns): self.columns=list(columns); return self
