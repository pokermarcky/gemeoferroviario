"""Aritmética configurável por AST restrita; nunca executa código de configuração."""
import ast
import math
import operator
from decimal import Decimal, ROUND_HALF_UP

def money(value):
    return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

def roundup(value, digits=0):
    factor = 10 ** digits
    return math.copysign(math.ceil(abs(value) * factor), value) / factor

OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
       ast.Div: operator.truediv, ast.Pow: operator.pow}
FUNCS = {'ROUNDUP': roundup, 'PI': lambda: math.pi, 'ceil': math.ceil,
         'floor': math.floor, 'min': min, 'max': max, 'abs': abs}

def evaluate(expression, context):
    # Resolve identificadores simples diretamente para manter o resultado
    # estável entre as versões do AST usadas localmente e no Streamlit Cloud.
    if isinstance(expression, str) and expression in context:
        result=context[expression]
        if not isinstance(result, (int, float)) or not math.isfinite(result):
            raise ValueError('Resultado numérico inválido.')
        return float(result)
    tree = ast.parse(str(expression).lstrip('=').replace('^', '**'), mode='eval')
    if len(list(ast.walk(tree))) > 300:
        raise ValueError('Expressão excede o limite de complexidade.')
    def walk(node):
        if isinstance(node, ast.Expression): return walk(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float): return node.value
        if isinstance(node, ast.Name) and node.id in context: return context[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            left, right = walk(node.left), walk(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 10: raise ValueError('Potência não permitida.')
            return OPS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            return -walk(node.operand) if isinstance(node.op, ast.USub) else walk(node.operand)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FUNCS and not node.keywords:
            return FUNCS[node.func.id](*[walk(a) for a in node.args])
        raise ValueError(f'Expressão não permitida: {expression}')
    result = walk(tree)
    if not isinstance(result, (int, float)) or not math.isfinite(result):
        raise ValueError('Resultado numérico inválido.')
    return float(result)
