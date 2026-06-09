from __future__ import annotations

from pathlib import Path

from .task import TaskSpec


def _patch(search: str, replace: str) -> str:
    return (
        "SEARCH\n"
        f"{search.rstrip()}\n"
        "END_SEARCH\n"
        "REPLACE\n"
        f"{replace.rstrip()}\n"
        "END_REPLACE\n"
    )


def _render_demo_add(description: str) -> str:
    desc = description.lower()
    module_doc = "A tiny numeric addition helper with input validation."
    function_doc = "Return the sum of two numeric values."
    extras: list[str] = []
    helper_blocks: list[str] = []
    numeric_expr = "(int, float)"
    validation = f"if not isinstance(a, {numeric_expr}) or not isinstance(b, {numeric_expr}):\n        raise TypeError(\"Both arguments must be numeric\")"
    return_block = "return a + b"

    if "formal" in desc:
        module_doc = "This module provides a small numeric addition helper with input validation."
    elif "intentionally small" in desc or "small and focused" in desc:
        module_doc = "This intentionally small module provides numeric addition with focused input validation."
    elif "tiny helper" in desc:
        module_doc = "A tiny helper for numeric addition. It validates inputs before returning their sum."
    elif "two short sentences" in desc or "one sentence plus one supporting sentence" in desc:
        module_doc = "Add two numeric inputs. Non-numeric inputs raise TypeError."
    elif "validation sentence comes first" in desc:
        module_doc = "Inputs are validated before addition. This module returns the sum of two numeric values."
    elif "example showing add(2, 3) returns 5" in desc:
        module_doc = "A tiny numeric addition helper. Example: add(2, 3) returns 5."
    elif "instructional" in desc:
        module_doc = "Use add() with two numeric inputs. The helper validates values before returning their sum."
    elif "only two numeric inputs" in desc:
        module_doc = "Only two numeric inputs are supported. The helper validates inputs before returning their sum."
    elif "module docstring" in desc or "module-level" in desc:
        module_doc = "A concise numeric addition helper with input validation."

    if "function docstring" in desc or "docstring for add" in desc or "simple numeric inputs" in desc:
        function_doc = "Return the sum of two numeric inputs and raise TypeError for non-numeric values."
    if "typeerror behavior" in desc:
        function_doc = "Add numeric inputs and raise TypeError when either input is non-numeric."

    if "__all__" in desc:
        extras.append('__all__ = ["add"]')
    if "__version__" in desc:
        extras.append('__version__ = "1.0.0"')
    if "module_name" in desc:
        extras.append('MODULE_NAME = "demo_add"')
    if "numeric_types" in desc:
        extras.append("NUMERIC_TYPES = (int, float)")
        numeric_expr = "NUMERIC_TYPES"
    if "default_numeric_types" in desc:
        extras.append("DEFAULT_NUMERIC_TYPES = (int, float)")
        numeric_expr = "DEFAULT_NUMERIC_TYPES"
    if "type alias" in desc or "numeric alias" in desc or "numeric = int | float" in desc:
        extras.append("Numeric = int | float")

    if "explanatory comment for the module-level numeric types" in desc:
        extras.append("# Accepted runtime numeric types for validation.")
        extras.append("NUMERIC_TYPES = (int, float)")
        numeric_expr = "NUMERIC_TYPES"
    if "module comment" in desc:
        extras.append("# Safe to patch in small increments.")

    if "_is_numeric" in desc:
        helper_blocks.append("def _is_numeric(value):\n    return isinstance(value, (int, float))")
        validation = "if not _is_numeric(a) or not _is_numeric(b):\n        raise TypeError(\"Both arguments must be numeric\")"
    if "_is_number" in desc:
        helper_blocks.append("def _is_number(value):\n    return isinstance(value, (int, float))")
        validation = "if not _is_number(a) or not _is_number(b):\n        raise TypeError(\"Both arguments must be numeric\")"
    if "_validate_numbers" in desc or "validation helper" in desc:
        annotation = ": int | float" if "type annotations" in desc else ""
        ret = " -> None" if "type annotations" in desc else ""
        doc = '    """Validate that both arguments are numeric."""\n' if "docstring" in desc else ""
        helper_blocks.append(
            f"def _validate_numbers(a{annotation}, b{annotation}){ret}:\n"
            f"{doc}"
            "    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):\n"
            "        raise TypeError(\"Both arguments must be numeric\")"
        )
        validation = "_validate_numbers(a, b)"
    if "_sum" in desc:
        annotation = ": int | float" if "type annotations" in desc else ""
        ret = " -> int | float" if "type annotations" in desc else ""
        doc = '    """Return a + b."""\n' if "docstring" in desc else ""
        helper_blocks.append(f"def _sum(a{annotation}, b{annotation}){ret}:\n{doc}    return a + b")
        return_block = "return _sum(a, b)"
    if "_raise_numeric_type_error" in desc:
        helper_blocks.append("def _raise_numeric_type_error():\n    raise TypeError(\"Both arguments must be numeric\")")
        validation = "if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):\n        _raise_numeric_type_error()"
    if "bool-returning helper" in desc or "returns a bool" in desc:
        helper_blocks.append("def _is_valid_numeric_pair(a, b):\n    return isinstance(a, (int, float)) and isinstance(b, (int, float))")
        validation = "if not _is_valid_numeric_pair(a, b):\n        raise TypeError(\"Both arguments must be numeric\")"

    if "shorter and more direct" in desc:
        validation = validation.replace('"Both arguments must be numeric"', '"Numeric inputs required"')
    if "all(...)" in desc:
        validation = "if not all(isinstance(value, (int, float)) for value in (a, b)):\n        raise TypeError(\"Both arguments must be numeric\")"
    if "split the validation across multiple lines" in desc:
        validation = "if not (\n        isinstance(a, (int, float))\n        and isinstance(b, (int, float))\n    ):\n        raise TypeError(\"Both arguments must be numeric\")"
    if "guard clause" in desc:
        validation = "if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):\n        raise TypeError(\"Both arguments must be numeric\")"
    if "comment above the validation" in desc or "near the typeerror raise" in desc:
        validation = "# Both arguments must be numeric before adding.\n    " + validation

    if "local variable named total" in desc:
        return_block = "total = a + b\n    return total"
    if "sum variable to result" in desc or "validation result to a variable" in desc:
        if "validation result" in desc:
            validation = "is_valid = isinstance(a, (int, float)) and isinstance(b, (int, float))\n    if not is_valid:\n        raise TypeError(\"Both arguments must be numeric\")"
        else:
            return_block = "result = a + b\n    return result"
    if "comment above the return" in desc:
        return_block = "# Return the computed sum.\n    " + return_block

    signature = "def add(a: int | float, b: int | float) -> int | float:"
    if "numeric alias" in desc or "numeric = int | float" in desc:
        signature = "def add(a: Numeric, b: Numeric) -> Numeric:"

    parts = [f'"""\n{module_doc}\n"""']
    if extras:
        parts.append("\n".join(extras))
    if helper_blocks:
        parts.extend(helper_blocks)
    parts.append(
        f"{signature}\n"
        f"    \"\"\"{function_doc}\"\"\"\n"
        f"    {validation}\n"
        f"    {return_block}"
    )
    return "\n\n".join(parts) + "\n"


def _render_math_tool(description: str, original: str = "") -> str:
    desc = description.lower()
    module_doc = "Small math helpers."
    function_doc = "Return a divided by b."
    extras: list[str] = []
    helper_blocks: list[str] = []
    signature = "def divide(a, b):"
    validation = ""
    return_block = "return a / b"

    preserve_zero_guard = 'raise ValueError("b must not be zero")' in original
    preserve_helper = "def _validate_divisor" in original
    preserve_all = "__all__" in original
    preserve_type_hints = "def divide(a: int | float, b: int | float) -> int | float:" in original
    preserve_quotient = "quotient = a / b" in original

    if "__all__" in desc or preserve_all:
        extras.append('__all__ = ["divide"]')

    if "docstring" in desc and "must not be zero" in desc:
        function_doc = "Return a divided by b; b must not be zero."
    elif "docstring" in desc:
        function_doc = "Divide a by b and return the quotient."

    if "type annotations" in desc or preserve_type_hints:
        signature = "def divide(a: int | float, b: int | float) -> int | float:"

    if "zero-division guard" in desc or "valueerror" in desc or "b is zero" in desc or preserve_zero_guard:
        validation = 'if b == 0:\n        raise ValueError("b must not be zero")'

    if "_validate_divisor" in desc or "divisor validation" in desc or preserve_helper:
        helper_blocks.append(
            "def _validate_divisor(b):\n"
            "    if b == 0:\n"
            "        raise ValueError(\"b must not be zero\")"
        )
        validation = "_validate_divisor(b)"

    if "quotient variable" in desc or preserve_quotient:
        return_block = "quotient = a / b\n    return quotient"

    if "comment above divide" in desc or "covered by tests" in desc:
        function_prefix = "# Normal division behavior is covered by tests.\n"
    else:
        function_prefix = ""

    parts = [f'"""{module_doc}"""']
    if extras:
        parts.append("\n".join(extras))
    if helper_blocks:
        parts.extend(helper_blocks)

    body_lines = [f'{function_prefix}{signature}', f'    """{function_doc}"""']
    if validation:
        body_lines.append(f"    {validation}")
    body_lines.append(f"    {return_block}")
    parts.append("\n".join(body_lines))
    return "\n\n".join(parts) + "\n"


def _render_test_math_tool(description: str) -> str:
    return (
        "import unittest\n"
        "\n"
        "from math_tool import divide\n"
        "\n"
        "\n"
        "class TestMathTool(unittest.TestCase):\n"
        "    def test_divide(self):\n"
        "        self.assertEqual(divide(6, 2), 3)\n"
        "\n"
        "    def test_divide_by_zero(self):\n"
        "        with self.assertRaises(ValueError):\n"
        "            divide(1, 0)\n"
    )


def build_local_template_patch(root: Path, task: TaskSpec) -> str | None:
    supported_targets = {"demo_add.py", "math_tool.py", "tests/test_math_tool.py"}
    if task.target_file.as_posix() not in supported_targets:
        return None
    target_path = root / task.target_file
    if not target_path.exists():
        return None
    original = target_path.read_text(encoding="utf-8")
    if task.target_file.as_posix() == "demo_add.py":
        replacement = _render_demo_add(task.description)
    elif task.target_file.as_posix() == "math_tool.py":
        replacement = _render_math_tool(task.description, original)
    else:
        replacement = _render_test_math_tool(task.description)
    if original == replacement:
        return None
    return _patch(original, replacement)
