"""
Tests for CT Dose Tracker clinical calculation functions.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import ct_dose
from ct_dose import (
    calculate_meld_na,
    calculate_qtc,
    calculate_bmi_z,
    convert_hba1c,
    calculate_apri_fib4,
    calculate_score,
    assess_row,
    process_csv,
)
import tempfile
import os


class TestMeldNa:
    def test_basic_calculation(self):
        result = calculate_meld_na(bilirubin=2.0, creatinine=1.5, inr=1.2)
        assert "meld_na" in result
        assert "risk" in result
        assert result["meld_na"] >= 6
        assert result["meld_na"] <= 40

    def test_high_risk(self):
        result = calculate_meld_na(bilirubin=10.0, creatinine=5.0, inr=3.0, sodium=125)
        assert result["risk"] == "HIGH"

    def test_low_risk(self):
        result = calculate_meld_na(bilirubin=1.0, creatinine=1.0, inr=1.0, sodium=140)
        assert result["risk"] == "LOW"

    def test_none_values(self):
        result = calculate_meld_na(bilirubin=None, creatinine=None)
        assert "meld_na" in result
        assert isinstance(result["meld_na"], (int, float))

    def test_dialysis_adjustment(self):
        result_normal = calculate_meld_na(bilirubin=1.0, creatinine=1.0, dialysis=False)
        result_dialysis = calculate_meld_na(bilirubin=1.0, creatinine=1.0, dialysis=True)
        assert result_dialysis["meld_na"] >= result_normal["meld_na"]


class TestQtc:
    def test_basic_calculation(self):
        result = calculate_qtc(qt_ms=400, hr_bpm=60)
        assert "qtc_ms" in result
        assert "prolonged" in result

    def test_prolonged_qt(self):
        result = calculate_qtc(qt_ms=500, hr_bpm=60)
        assert result["prolonged"] is True

    def test_normal_qt(self):
        result = calculate_qtc(qt_ms=380, hr_bpm=70)
        assert result["prolonged"] is False

    def test_with_rr(self):
        result = calculate_qtc(qt_ms=400, rr_ms=1000)
        assert "qtc_ms" in result


class TestBmi:
    def test_basic_calculation(self):
        result = calculate_bmi_z(weight_kg=70, height_cm=175)
        assert "bmi" in result
        assert result["bmi"] > 0

    def test_pediatric(self):
        result = calculate_bmi_z(weight_kg=20, height_cm=110, age_months=60)
        assert "bmi" in result
        assert result["age_months"] == 60


class TestHba1c:
    def test_hba1c_to_eag(self):
        result = convert_hba1c(hba1c_percent=7.0)
        assert "hba1c_percent" in result
        assert "eag_mgdl" in result
        assert result["hba1c_percent"] == 7.0

    def test_eag_to_hba1c(self):
        result = convert_hba1c(eag_mgdl=154)
        assert "hba1c_percent" in result
        assert "eag_mgdl" in result

    def test_default_values(self):
        result = convert_hba1c()
        assert "hba1c_percent" in result
        assert "eag_mgdl" in result


class TestApriFib4:
    def test_basic_calculation(self):
        result = calculate_apri_fib4(ast_u_l=40, alt_u_l=40, platelets_109=200, age_years=40)
        assert "apri" in result
        assert "fib4" in result
        assert result["apri"] >= 0
        assert result["fib4"] >= 0

    def test_none_values(self):
        result = calculate_apri_fib4(ast_u_l=30)
        assert "apri" in result
        assert "fib4" in result


class TestAssessRow:
    def test_meld_na_path(self):
        result = assess_row({"bilirubin": 2.0, "creatinine": 1.5, "inr": 1.2})
        assert "meld_na" in result

    def test_qtc_path(self):
        result = assess_row({"qt_ms": 400, "hr_bpm": 60})
        assert "qtc_ms" in result

    def test_bmi_path(self):
        result = assess_row({"weight_kg": 70, "height_cm": 175})
        assert "bmi" in result

    def test_hba1c_path(self):
        result = assess_row({"hba1c_percent": 7.0})
        assert "eag_mgdl" in result

    def test_apri_path(self):
        result = assess_row({"ast_u_l": 40})
        assert "apri" in result

    def test_generic_score(self):
        result = assess_row({"value": 10, "qty": 2})
        assert "score" in result


class TestProcessCsv:
    def test_process_csv_basic(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            f.write("id,value,qty\n")
            f.write("A,10,2\n")
            f.write("B,20,3\n")
            input_path = f.name

        output_path = input_path + ".out.csv"
        try:
            results = process_csv(input_path, output_path)
            assert len(results) == 2
            assert os.path.exists(output_path)
            assert "score" in results[0]
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_process_csv_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            process_csv("/nonexistent/path/file.csv", "output.csv")


class TestCalculateScore:
    def test_basic_score(self):
        result = calculate_score(value=10, qty=2)
        assert "score" in result
        assert "inputs" in result
        assert result["inputs"] > 0

    def test_empty_inputs(self):
        result = calculate_score()
        assert "score" in result
        assert result["inputs"] == 1
