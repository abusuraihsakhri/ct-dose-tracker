"""CSV outputs must never promote user labels to spreadsheet formulas."""
import csv
from csv_safety import escape_csv_formula
from cli import main as cli_main


def test_formula_prefixes_and_numeric_literals():
    assert escape_csv_formula("=SUM(1,1)") == "'=SUM(1,1)"
    assert escape_csv_formula("  @HYPERLINK(1)") == "'  @HYPERLINK(1)"
    assert escape_csv_formula("-12.5") == "-12.5"
    assert escape_csv_formula("+1.2e-2") == "+1.2e-2"


def test_legacy_batch_export_escapes_spreadsheet_formulas(tmp_path):
    inp, out = tmp_path / "tasks.csv", tmp_path / "results.csv"
    inp.write_text("task_id,target_identifier,primary_metric\n=2+3,KEY-01,10\n", encoding="utf8")
    assert cli_main(["batch", "--input", str(inp), "--output", str(out)]) == 0
    with out.open(newline="", encoding="utf8") as stream:
        row = next(csv.DictReader(stream))
    assert row["task_id"] == "'=2+3"
    assert row["primary_metric"] == "10"
