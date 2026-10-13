"""Neutralize CSV cells that spreadsheet software could interpret as formulas."""
import re

_NUMERIC_LITERAL = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\Z")


def escape_csv_formula(value):
    """Escape potentially executable spreadsheet cells while preserving numeric literals."""
    if not isinstance(value, str):
        return value
    stripped = value.lstrip()
    if stripped.startswith(("=", "+", "-", "@")) and not _NUMERIC_LITERAL.fullmatch(stripped):
        return "'" + value
    return value
