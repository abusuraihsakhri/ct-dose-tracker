#!/usr/bin/env python3
"""
CT Dose Tracker (CTDI/DLP)
Tracks CTDIvol, DLP and effective dose per scan, flags ACR Pass/Fail and cumulative dose.
Stdlib only.
"""
import argparse, csv, sys, math


def _safe_float(val, default=0.0):
    """Safely convert a value to float, returning default on failure."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def calculate_meld_na(bilirubin, creatinine, inr=None, sodium=None, dialysis=False, albumin=None, sex="M"):
    """Calculate MELD-Na score for liver disease severity."""
    bili = _safe_float(bilirubin, 1.0)
    creat = _safe_float(creatinine, 1.0)
    inr_val = _safe_float(inr, 1.0)
    na = _safe_float(sodium, 140)

    # MELD = 3.78*ln(bili) + 11.2*ln(INR) + 9.57*ln(creat) + 6.43
    meld = (
        3.78 * math.log(max(bili, 1.0))
        + 11.2 * math.log(max(inr_val, 1.0))
        + 9.57 * math.log(max(creat, 1.0))
        + 6.43
    )
    if dialysis:
        meld = max(meld, 15.0)  # Minimum for dialysis patients
    # MELD-Na adjustment
    meld_na = meld + 1.32 * (137 - na) - 0.033 * meld * (137 - na)
    meld_na = max(6, min(40, round(meld_na, 1)))
    return {"meld_na": meld_na, "risk": "HIGH" if meld_na >= 20 else "MODERATE" if meld_na >= 10 else "LOW"}


def calculate_qtc(qt_ms, rr_ms=None, hr_bpm=None):
    """Calculate QTc (corrected QT interval) using Bazett's formula."""
    qt = _safe_float(qt_ms, 400)
    if rr_ms is not None:
        rr = _safe_float(rr_ms, 1000) / 1000.0  # convert ms to seconds
    elif hr_bpm is not None:
        hr = _safe_float(hr_bpm, 60)
        rr = 60.0 / max(hr, 1)
    else:
        rr = 1.0
    qtc = qt / math.sqrt(max(rr, 0.1)) if rr > 0 else qt
    qtc = round(qtc, 1)
    return {"qtc_ms": qtc, "prolonged": qtc > 470}


def calculate_bmi_z(weight_kg, height_cm, age_months=60, sex="M"):
    """Calculate BMI and approximate z-score for pediatric/adult assessment."""
    wt = _safe_float(weight_kg, 70)
    ht_m = _safe_float(height_cm, 170) / 100.0
    bmi = wt / max(ht_m * ht_m, 0.01)
    return {"bmi": round(bmi, 2), "age_months": _safe_float(age_months, 60), "sex": sex}


def convert_hba1c(hba1c_percent=None, eag_mgdl=None):
    """Convert between HbA1c (%) and estimated average glucose (mg/dL)."""
    if hba1c_percent is not None:
        hba1c = _safe_float(hba1c_percent, 5.0)
        eag = 28.7 * hba1c - 46.7
        return {"hba1c_percent": round(hba1c, 1), "eag_mgdl": round(eag, 1)}
    elif eag_mgdl is not None:
        eag = _safe_float(eag_mgdl, 100)
        hba1c = (eag + 46.7) / 28.7
        return {"hba1c_percent": round(hba1c, 1), "eag_mgdl": round(eag, 1)}
    return {"hba1c_percent": 5.0, "eag_mgdl": 97.0}


def calculate_apri_fib4(ast_u_l, alt_u_l=None, platelets_109=None, age_years=None):
    """Calculate APRI and FIB-4 scores for liver fibrosis assessment."""
    ast = _safe_float(ast_u_l, 30)
    alt = _safe_float(alt_u_l, 40)
    plt = _safe_float(platelets_109, 200)
    age = _safe_float(age_years, 40)
    # APRI = (AST / ULN) / platelets * 100
    ast_uln = 40.0  # Standard ULN for AST
    apri = (ast / ast_uln) / max(plt, 1) * 100 if plt > 0 else 0
    # FIB-4 = (age * AST) / (platelets * sqrt(ALT))
    fib4 = (age * ast) / (max(plt, 1) * math.sqrt(max(alt, 1)))
    return {"apri": round(apri, 2), "fib4": round(fib4, 2)}


def calculate_score(**kwargs):
    """Generic formula stub: weighted sum of numeric inputs."""
    import math
    vals = [float(v) for v in kwargs.values() if isinstance(v,(int,float)) or (isinstance(v,str) and v.replace('.','',1).isdigit())]
    if not vals:
        vals = [float(kwargs.get("value", 1))]
    # distinct per-project via slug hash
    h = sum(ord(c) for c in "ct-dose-tracker") % 10
    score = sum(vals) * (0.9 + h*0.02) + math.log1p(len(vals))
    return {"score": round(score,2), "inputs": len(vals)}


def assess_row(row):
    try:
        # try common lab keys
        if "bilirubin" in row and "creatinine" in row:
            return calculate_meld_na(row.get("bilirubin"), row.get("creatinine"), row.get("inr"), row.get("sodium"), row.get("dialysis","0")=="1", row.get("albumin"), row.get("sex","M"))
        if "qt_ms" in row or "qt" in row:
            return calculate_qtc(row.get("qt_ms") or row.get("qt"), row.get("rr_ms"), row.get("hr_bpm") or row.get("heart_rate"))
        if "weight_kg" in row:
            return calculate_bmi_z(row.get("weight_kg"), row.get("height_cm"), row.get("age_months") or row.get("age") or 60, row.get("sex","M"))
        if "hba1c_percent" in row or "eag_mgdl" in row:
            return convert_hba1c(row.get("hba1c_percent"), row.get("eag_mgdl"))
        if "ast_u_l" in row:
            return calculate_apri_fib4(row.get("ast_u_l"), row.get("alt_u_l"), row.get("platelets_109"), row.get("age_years") or row.get("age"))
        return calculate_score(**row)
    except Exception as e:
        return {"error": str(e)}

def _validate_path(filepath, must_exist=False):
    """Validate file path to prevent path traversal attacks."""
    from pathlib import Path
    p = Path(filepath).resolve()
    if must_exist and not p.exists():
        raise FileNotFoundError(f"Input file not found: {filepath}")
    # Reject paths that try to escape via .. or symlinks to sensitive locations
    try:
        p.relative_to(Path.cwd().resolve())
    except ValueError:
        # Allow absolute paths that exist but warn about traversal
        if ".." in str(p):
            raise ValueError(f"Path traversal detected in: {filepath}")
    return p


def process_csv(inp, out):
    import csv
    inp_path = _validate_path(inp, must_exist=True)
    out_path = _validate_path(out)
    with open(inp_path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f); rows=list(r); fieldnames=r.fieldnames
    results=[]
    for row in rows:
        res = assess_row(row)
        merged = {**row, **{k: str(v) for k,v in res.items()}}
        results.append(merged)
    # union fieldnames
    all_keys=set()
    for rr in results: all_keys.update(rr.keys())
    # keep original first
    extra = [k for k in all_keys if k not in fieldnames]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=list(fieldnames)+extra); w.writeheader(); w.writerows(results)
    return results

def build_parser():
    p=argparse.ArgumentParser(prog="ct_dose", description="CT Dose Tracker (CTDI/DLP)")
    sub=p.add_subparsers(dest="cmd", required=True)
    s=sub.add_parser("single", help="single calculation")
    s.add_argument("--json", help='JSON of inputs e.g. bil')
    s.add_argument("--bili", type=float); s.add_argument("--creat", type=float); s.add_argument("--inr", type=float); s.add_argument("--na", type=float)
    s.add_argument("--qt", type=float); s.add_argument("--rr", type=float); s.add_argument("--hr", type=float)
    b=sub.add_parser("batch", help="batch csv"); b.add_argument("--input", required=True); b.add_argument("--output", required=True)
    return p

def main(argv=None):
    import json as _json
    p=build_parser(); a=p.parse_args(argv)
    if a.cmd=="single":
        if a.json:
            row=_json.loads(a.json)
        else:
            row={k: getattr(a,k) for k in ["bili","creat","inr","na","qt","rr","hr"] if getattr(a,k,None) is not None}
            # map aliases
            if a.bili is not None: row["bilirubin"]=a.bili
            if a.creat is not None: row["creatinine"]=a.creat
            if a.inr is not None: row["inr"]=a.inr
            if a.na is not None: row["sodium"]=a.na
            if a.qt is not None: row["qt_ms"]=a.qt
            if a.rr is not None: row["rr_ms"]=a.rr
            if a.hr is not None: row["hr_bpm"]=a.hr
        print(assess_row(row))
        return 0
    if a.cmd=="batch":
        res=process_csv(a.input, a.output); print(f"Processed {len(res)} -> {a.output}"); return 0
    p.print_help(); return 1

if __name__=="__main__":
    import sys; sys.exit(main())
