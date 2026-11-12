"""Safe arithmetic evaluator for chat expressions."""
import ast
import re
from decimal import Decimal, localcontext

FOLLOWUP = re.compile(r"(?:please\s+)?(?:do the math|calculate (?:it|that)|solve (?:it|that)|what(?:'s| is) the (?:answer|result))[.!?\s]*$", re.I)

def extract(text):
    text = re.sub(r"^(?:please\s+)?(?:calculate|compute|evaluate|solve|what is|what's)\s*:?[ \t]*", "", text.strip(), flags=re.I)
    text = text.rstrip("?.! ").replace("×", "*").replace("÷", "/").replace("−", "-").replace("^", "**").replace(",", "")
    if len(text) > 250 or not re.fullmatch(r"[\d\s.()+*/%\-]+", text): return None
    if not re.search(r"\d\s*(?:\*\*|[+*/%\-])\s*[\d(]|\)\s*[+*/%\-]", text): return None
    return text

def resolve(text, prior):
    direct = extract(text)
    if direct: return direct
    if FOLLOWUP.fullmatch(text.strip()):
        for message in reversed(prior):
            if message.get("role") == "user":
                previous = extract(message.get("content", ""))
                if previous: return previous
    return None

def evaluate(expression):
    if len(expression) > 250: raise ValueError("Expression too long")
    tree = ast.parse(expression, mode="eval")
    counter = [0]
    with localcontext() as ctx:
        ctx.prec = 100
        def visit(node):
            counter[0] += 1
            if counter[0] > 80: raise ValueError("Expression too complex")
            if isinstance(node, ast.Constant) and type(node.value) in (int,float):
                if len(str(node.value)) > 100: raise ValueError("Number too large")
                return Decimal(str(node.value))
            if isinstance(node, ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
                value = visit(node.operand)
                return value if isinstance(node.op,ast.UAdd) else -value
            if isinstance(node, ast.BinOp):
                a,b = visit(node.left),visit(node.right)
                if isinstance(node.op,ast.Add): return a+b
                if isinstance(node.op,ast.Sub): return a-b
                if isinstance(node.op,ast.Mult): return a*b
                if isinstance(node.op,ast.Div): return a/b
                if isinstance(node.op,ast.Mod): return a%b
                if isinstance(node.op,ast.Pow):
                    if b != b.to_integral_value() or abs(b)>100 or abs(a)>Decimal('1e100'): raise ValueError("Exponent too large")
                    return a**int(b)
            raise ValueError("Unsupported expression")
        try: result = visit(tree.body)
        except (ArithmeticError, ZeroDivisionError) as exc: raise ValueError("Division by zero or arithmetic overflow") from exc
    if not result.is_finite(): raise ValueError("Non-finite result")
    output = format(result,"f")
    if "." in output: output=output.rstrip("0").rstrip(".")
    if len(output)>300: raise ValueError("Result too long")
    return output
