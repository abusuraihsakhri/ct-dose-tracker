"""Regression tests for actual CT dose functionality."""
import csv
import math

import pytest

from dose_metrics import DoseInputError, calculate_ct_dose, summarize_dose_exams
from ct_dose import assess_row, main, process_csv


def test_ctdi_length_to_dlp():
    value = calculate_ct_dose(ctdi_vol_mgy=12, scan_length_cm=35)
    assert value["dlp_mgy_cm"] == 420
    assert value["dlp_source"] == "calculated"
    assert value["effective_msv"] is None


def test_reported_dlp_has_priority():
    value = calculate_ct_dose(12, 35, 450, 0.014)
    assert value["dlp_source"] == "reported"
    assert value["calculated_dlp_mgy_cm"] == 420
    assert value["dlp_mgy_cm"] == 450
    assert value["effective_msv"] == pytest.approx(6.3)


def test_dlp_only_and_zero():
    assert calculate_ct_dose(dlp_mgy_cm=0)["dlp_mgy_cm"] == 0


@pytest.mark.parametrize("kwargs", [
    {}, {"ctdi_vol_mgy": 10}, {"scan_length_cm": 20},
    {"ctdi_vol_mgy": -1, "scan_length_cm": 20},
    {"ctdi_vol_mgy": "nan", "scan_length_cm": 20},
    {"ctdi_vol_mgy": 10, "scan_length_cm": 0},
    {"dlp_mgy_cm": math.inf}, {"dlp_mgy_cm": 300, "k_msv_per_mgy_cm": -0.1},
])
def test_bad_inputs(kwargs):
    with pytest.raises(DoseInputError):
        calculate_ct_dose(**kwargs)


def test_total_dlp_and_partial_estimates():
    exams = [
        calculate_ct_dose(10, 30, k_msv_per_mgy_cm=0.014),
        calculate_ct_dose(dlp_mgy_cm=200),
    ]
    total = summarize_dose_exams(exams)
    assert total["total_dlp_mgy_cm"] == 500
    assert total["partial_effective_msv"] == pytest.approx(4.2)
    assert total["effective_estimate_count"] == 1


def test_dispatch_ct_dose_and_retains_legacy():
    assert assess_row({"ctdi_vol_mgy": "10", "scan_length_cm": "30"})["dlp_mgy_cm"] == 300
    assert "qtc_ms" in assess_row({"qt_ms": "400", "hr_bpm": "60"})


def test_cli_single_ct_dose(capsys):
    assert main(["single", "--ctdi-vol", "10", "--scan-length", "30"]) == 0
    assert "'dlp_mgy_cm': 300.0" in capsys.readouterr().out


def test_batch_ct_dose(tmp_path):
    inp, out = tmp_path / "input.csv", tmp_path / "result.csv"
    inp.write_text("protocol,ctdi_vol_mgy,scan_length_cm,k_msv_per_mgy_cm\nChest,10,30,0.014\n", encoding="utf8")
    results = process_csv(str(inp), str(out))
    assert results[0]["dlp_mgy_cm"] == "300.0"
    with out.open(newline="") as file:
        assert next(csv.DictReader(file))["effective_msv"] == "4.2"


def test_empty_csv_rejected(tmp_path):
    file = tmp_path / "empty.csv"
    file.write_text("", encoding="utf8")
    with pytest.raises(ValueError, match="header"):
        process_csv(str(file), str(tmp_path / "out.csv"))


def test_intermediate_and_cumulative_overflow_rejected():
    with pytest.raises(DoseInputError, match="Calculated DLP"):
        calculate_ct_dose(ctdi_vol_mgy=1e308, scan_length_cm=10, dlp_mgy_cm=20)
    with pytest.raises(DoseInputError, match="Cumulative DLP"):
        summarize_dose_exams([calculate_ct_dose(dlp_mgy_cm=1e308)] * 2)
    with pytest.raises(DoseInputError, match="Cumulative effective"):
        summarize_dose_exams([calculate_ct_dose(dlp_mgy_cm=1e200, k_msv_per_mgy_cm=1e108)] * 2)


def test_cli_invalid_dose_returns_nonzero(capsys):
    assert main(["single", "--ctdi-vol", "10"]) == 2
    assert "Error:" in capsys.readouterr().err
    assert main(["single", "--json", "{bad"]) == 2
    assert main(["single", "--json", "[]"]) == 2


def test_python_csv_export_neutralizes_formulas(tmp_path):
    inp, out = tmp_path / "input.csv", tmp_path / "result.csv"
    inp.write_text("protocol,dlp_mgy_cm\n=2+3,200\n", encoding="utf8")
    rows = process_csv(str(inp), str(out))
    assert rows[0]["protocol"] == "=2+3"  # The in-memory record is unchanged.
    with out.open(newline="", encoding="utf8") as file:
        record = next(csv.DictReader(file))
    assert record["protocol"] == "'=2+3"
    assert record["dlp_mgy_cm"] == "200"
