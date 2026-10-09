"""Regression for CLI CSV critical-flag parsing."""
import pytest
from cli import parse_csv_bool

@pytest.mark.parametrize("raw,expected", [
    ("false", False), ("False", False), ("0", False),
    ("", False), (None, False), ("TRUE", True), ("yes", True), ("1", True),
])
def test_csv_bool(raw, expected):
    assert parse_csv_bool(raw) is expected

def test_bad_bool_rejected():
    with pytest.raises(ValueError):
        parse_csv_bool("definitely")
