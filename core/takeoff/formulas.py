"""Safe formula engine for user-defined takeoff formulas."""
import ast,operator
_OP={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.Pow:operator.pow,ast.USub:operator.neg}
def evaluate(expression,variables):
    tree=ast.parse(expression,mode="eval")
    def ev(n):
        if isinstance(n,ast.Expression): return ev(n.body)
        if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)): return float(n.value)
        if isinstance(n,ast.Name): return float(variables[n.id])
        if isinstance(n,ast.UnaryOp) and type(n.op) in _OP: return _OP[type(n.op)](ev(n.operand))
        if isinstance(n,ast.BinOp) and type(n.op) in _OP: return _OP[type(n.op)](ev(n.left),ev(n.right))
        raise ValueError("فرمول شامل عملگر یا مقدار غیرمجاز است")
    return ev(tree)
