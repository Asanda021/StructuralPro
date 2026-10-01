"""Safe arithmetic formulas for takeoff quantities."""
from __future__ import annotations
import ast,operator as op
_BIN={ast.Add:op.add,ast.Sub:op.sub,ast.Mult:op.mul,ast.Div:op.truediv,ast.FloorDiv:op.floordiv,ast.Mod:op.mod,ast.Pow:op.pow}
_UN={ast.UAdd:op.pos,ast.USub:op.neg}
class FormulaError(ValueError): pass
def evaluate(expression:str,variables:dict[str,float]|None=None)->float:
    tree=ast.parse(str(expression),mode="eval"); env={k:float(v) for k,v in (variables or {}).items()}
    def visit(n):
        if isinstance(n,ast.Expression): return visit(n.body)
        if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)): return float(n.value)
        if isinstance(n,ast.Name):
            if n.id not in env: raise FormulaError(f"متغیر ناشناخته: {n.id}")
            return env[n.id]
        if isinstance(n,ast.BinOp) and type(n.op) in _BIN:
            try:return _BIN[type(n.op)](visit(n.left),visit(n.right))
            except ZeroDivisionError as e:raise FormulaError("تقسیم بر صفر مجاز نیست") from e
        if isinstance(n,ast.UnaryOp) and type(n.op) in _UN:return _UN[type(n.op)](visit(n.operand))
        raise FormulaError("فرمول فقط شامل اعداد، متغیرها و عملگرهای حسابی است")
    result=float(visit(tree))
    if not result==result or abs(result)==float("inf"):raise FormulaError("نتیجه فرمول معتبر نیست")
    return result
