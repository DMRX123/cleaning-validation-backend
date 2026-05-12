import re
import math

def parse_excel_formula(formula: str) -> dict:
    """
    Parse Excel formula into components
    Example: "=IFERROR((D4*1000000)/H4,"")"
    """
    if not formula or not formula.startswith("="):
        return {"type": "value", "value": formula}
    
    formula = formula[1:]  # Remove =
    
    # Check for IFERROR
    if formula.startswith("IFERROR"):
        match = re.match(r'IFERROR\((.*?),(.*?)\)$', formula)
        if match:
            return {
                "type": "IFERROR",
                "expression": match.group(1),
                "fallback": match.group(2)
            }
    
    # Check for AND
    if formula.startswith("AND"):
        match = re.match(r'AND\((.*?)\)$', formula)
        if match:
            conditions = [c.strip() for c in match.group(1).split(",")]
            return {
                "type": "AND",
                "conditions": conditions
            }
    
    # Check for MIN
    if formula.startswith("MIN"):
        match = re.match(r'MIN\((.*?)\)$', formula)
        if match:
            values = [v.strip() for v in match.group(1).split(",")]
            return {
                "type": "MIN",
                "values": values
            }
    
    return {"type": "expression", "expression": formula}


def evaluate_formula(parsed_formula: dict, context: dict) -> any:
    """
    Evaluate parsed Excel formula with given context
    """
    formula_type = parsed_formula.get("type")
    
    if formula_type == "value":
        return parsed_formula.get("value")
    
    if formula_type == "IFERROR":
        try:
            return evaluate_expression(parsed_formula["expression"], context)
        except:
            return parsed_formula.get("fallback", "")
    
    if formula_type == "AND":
        results = []
        for cond in parsed_formula["conditions"]:
            try:
                result = evaluate_expression(cond, context)
                results.append(bool(result))
            except:
                results.append(False)
        return all(results)
    
    if formula_type == "MIN":
        values = []
        for val in parsed_formula["values"]:
            try:
                values.append(float(evaluate_expression(val, context)))
            except:
                pass
        return min(values) if values else 0
    
    if formula_type == "expression":
        return evaluate_expression(parsed_formula["expression"], context)
    
    return None


def evaluate_expression(expression: str, context: dict) -> float:
    """
    Evaluate mathematical expression with context variables
    Supports: *, /, +, -, ()
    """
    # Replace context variables
    for key, value in context.items():
        if isinstance(value, (int, float)):
            expression = expression.replace(key, str(value))
    
    # Safe evaluation
    try:
        # Only allow mathematical operations
        allowed_chars = set("0123456789+-*/(). ")
        if all(c in allowed_chars for c in expression):
            return eval(expression)
        return 0
    except:
        return 0


def excel_like_calculation(formula: str, row_data: dict) -> any:
    """
    Direct Excel-like calculation
    """
    parsed = parse_excel_formula(formula)
    return evaluate_formula(parsed, row_data)