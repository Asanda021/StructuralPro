"""Undo/redo integration helpers for mutable project dictionaries."""
from __future__ import annotations
from copy import deepcopy
from .undo import CommandStack

class ProjectHistory:
    def __init__(self, project: dict, limit=100):
        self.project=project
        self.stack=CommandStack(limit)
    def set_value(self, path: list[str], value):
        old=deepcopy(self.project)
        new=deepcopy(self.project)
        cur=new
        for key in path[:-1]: cur=cur[key]
        cur[path[-1]]=value
        def do(): self.project.clear(); self.project.update(deepcopy(new))
        def undo(): self.project.clear(); self.project.update(deepcopy(old))
        self.stack.execute(do,undo)
    def undo(self): return self.stack.undo()
    def redo(self): return self.stack.redo()
