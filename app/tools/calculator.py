"""Calculator Tool — evaluates mathematical expressions safely."""

import time
import logging
import math

from langchain.tools import tool

logger = logging.getLogger(__name__)


@tool
def calculator(expression: str) -> str:
    """
    Evaluate a mathematical expression. Supports arithmetic, algebra,
    trigonometry, logarithms, and common math functions.

    Examples:
        - "25 * 48 + 132"
        - "sqrt(144)"
        - "sin(pi/4)"
        - "log(1000, 10)"
        - "2**10"
        - "(15 + 25) / 4"

    Args:
        expression: Mathematical expression to evaluate.

    Returns:
        The computed result as a string.
    """
    start = time.time()
    logger.info(f"[Calculator] Evaluating: {expression}")

    try:
        # Clean the expression
        cleaned = _sanitize_expression(expression)

        # Try sympy first for symbolic math
        try:
            result = _sympy_evaluate(cleaned)
        except Exception:
            # Fallback to safe eval
            result = _safe_evaluate(cleaned)

        duration = (time.time() - start) * 1000
        logger.info(f"[Calculator] Result: {result} (in {duration:.1f}ms)")

        return f"Result: {result}"

    except Exception as e:
        logger.error(f"[Calculator] Error: {e}")
        return f"Calculation error: {str(e)}. Please check the expression."


def _sanitize_expression(expr: str) -> str:
    """Clean and validate the expression."""
    # Remove common natural language
    replacements = {
        "what is": "",
        "calculate": "",
        "compute": "",
        "solve": "",
        "×": "*",
        "÷": "/",
        "^": "**",
    }
    result = expr.lower().strip()
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result.strip()


def _sympy_evaluate(expression: str) -> str:
    """Evaluate using sympy for robust math parsing."""
    from sympy import sympify, N, pi, E, oo
    from sympy.parsing.sympy_parser import (
        parse_expr,
        standard_transformations,
        implicit_multiplication_application,
        convert_xor,
    )

    transformations = standard_transformations + (
        implicit_multiplication_application,
        convert_xor,
    )

    parsed = parse_expr(expression, transformations=transformations)
    result = N(parsed)

    # Format nicely
    if result == int(result):
        return str(int(result))
    return str(round(float(result), 10))


def _safe_evaluate(expression: str) -> str:
    """Safe eval fallback with restricted namespace."""
    allowed_names = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "log2": math.log2,
        "pi": math.pi,
        "e": math.e,
        "ceil": math.ceil,
        "floor": math.floor,
        "factorial": math.factorial,
    }

    # Block dangerous builtins
    result = eval(expression, {"__builtins__": {}}, allowed_names)

    if isinstance(result, float) and result == int(result):
        return str(int(result))
    return str(result)
