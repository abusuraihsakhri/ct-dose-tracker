"""CT scanner-output calculations (not patient-specific absorbed dose).

AAPM Report 96: https://www.aapm.org/pubs/reports/detail.asp?docid=97
CTDIvol is a phantom-based scanner-output index. DLP is a surrogate
rather than a direct measure of organ absorbed dose. E ~= DLP * k is
a population-level estimate, not an individual risk prediction.
"""
import math


class DoseInputError(ValueError):
    """Invalid or incomplete CT dose measurements."""


def _nonnegative(value, name, *, positive=False):
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool):
        raise DoseInputError(f"{name} must be a number")
    try:
        val = float(value)
    except (TypeError, ValueError) as exc:
        raise DoseInputError(f"{name} must be a number") from exc
    if not math.isfinite(val) or val < 0 or (positive and val == 0):
        qualifier = "positive" if positive else "non-negative"
        raise DoseInputError(f"{name} must be a finite {qualifier} number")
    return val


def calculate_ct_dose(
    ctdi_vol_mgy=None,
    scan_length_cm=None,
    dlp_mgy_cm=None,
    k_msv_per_mgy_cm=None,
):
    """Calculate DLP and optional approximate effective dose.

    Uses scanner-reported DLP when provided. If absent, calculates DLP
    from CTDIvol x scan length. An explicit conversion coefficient k is
    required for the optional E estimate.
    """
    ctdi = _nonnegative(ctdi_vol_mgy, "CTDIvol")
    length = _nonnegative(scan_length_cm, "Scan length", positive=True)
    reported = _nonnegative(dlp_mgy_cm, "Reported DLP")
    k = _nonnegative(k_msv_per_mgy_cm, "Conversion coefficient")
    if reported is None and (ctdi is None or length is None):
        raise DoseInputError(
            "Provide reported DLP or both CTDIvol and scan length"
        )
    calculated = ctdi * length if ctdi is not None and length is not None else None
    dlp = reported if reported is not None else calculated
    if not math.isfinite(dlp):
        raise DoseInputError("Calculated DLP exceeds numeric range")
    effective = dlp * k if k is not None else None
    if effective is not None and not math.isfinite(effective):
        raise DoseInputError("Effective dose estimate exceeds numeric range")
    return {
        "ctdi_vol_mgy": ctdi,
        "scan_length_cm": length,
        "dlp_mgy_cm": dlp,
        "dlp_source": "reported" if reported is not None else "calculated",
        "calculated_dlp_mgy_cm": calculated,
        "k_msv_per_mgy_cm": k,
        "effective_msv": effective,
    }


def summarize_dose_exams(exams):
    """Return totals and the number of exams contributing an E estimate."""
    total_dlp = 0.0
    effective = 0.0
    known = 0
    count = 0
    for exam in exams:
        count += 1
        total_dlp += exam["dlp_mgy_cm"]
        if exam["effective_msv"] is not None:
            known += 1
            effective += exam["effective_msv"]
    return {
        "examinations": count,
        "total_dlp_mgy_cm": total_dlp,
        "partial_effective_msv": effective if known else None,
        "effective_estimate_count": known,
    }
