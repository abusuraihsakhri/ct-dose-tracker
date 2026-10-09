# CT Dose Tracker

### [Open the Live Application →](https://abusuraihsakhri.github.io/ct-dose-tracker/)

A browser and Python worksheet for computed tomography scanner-output dose metrics: **CTDIvol** (mGy), **dose–length product (DLP)** (mGy·cm), and an optional **approximate effective dose** (mSv).

## Browser application

The root `index.html` runs without a backend or build step:

- Add examinations using scanner-reported DLP, or CTDIvol and scan length.
- Optionally provide a DLP-to-effective-dose coefficient (`k`); no coefficient is inferred automatically.
- View cumulative DLP and the sum of *available* effective-dose estimates, including their coverage.
- Import CSV examination measurements and export a local CSV summary (maximum 2,000 rows and 2 MB per import).
- Remove entries or clear the session. Data stay in the browser tab and are not automatically saved or uploaded.

To run locally:

```bash
python -m http.server 8000
# Open http://localhost:8000/
```

The application uses vanilla JavaScript and runs directly on GitHub Pages. Python/Pyodide is **not required** for the browser worksheet.

CSV headers: `protocol,ctdi_vol_mgy,scan_length_cm,dlp_mgy_cm,k_msv_per_mgy_cm`. DLP, or both CTDIvol and scan length, is required for each examination. The protocol label should not contain patient identifiers.

## Interpretation and limitations

- `DLP = CTDIvol × scan length` is used when DLP is not provided. The scanner-reported DLP takes precedence.
- When an appropriate coefficient is explicitly provided, `E ≈ DLP × k` gives an **approximate population-level** effective-dose estimate, **not** individual patient absorbed dose or cancer risk.
- Conversion coefficients depend on anatomical region, patient age, scanning technique, and reference phantom. The illustrative adult-chest example uses `k = 0.014 mSv/(mGy·cm)` from AAPM Report 96.
- The worksheet does **not** calculate size-specific dose estimates (SSDE), determine clinical appropriateness, or issue ACR pass/fail judgments. Diagnostic reference levels are not individual patient dose limits.

References: [AAPM Report 96](https://www.aapm.org/pubs/reports/detail.asp?docid=97), [AAPM Report 204](https://www.aapm.org/pubs/reports/detail.asp?docid=143).

## Python calculations and CLI

Python 3.10+ is supported. The CT dose module uses only the standard library; the separate legacy supervisor/API functions require packages in `requirements.txt`.

```bash
python -m pip install -r requirements.txt
python ct_dose.py single --ctdi-vol 10 --scan-length 30 --k 0.014
python ct_dose.py single --json '{"dlp_mgy_cm": 450, "k_msv_per_mgy_cm": 0.014}'
python ct_dose.py batch --input my_exams.csv --output results.csv
```

The new `dose_metrics.calculate_ct_dose()` function accepts CTDIvol, scan length, reported DLP and an optional conversion coefficient with explicit finite/non-negative validation; `summarize_dose_exams()` totals records.

The repository also retains its earlier *separate* MELD-Na, QTc, BMI, HbA1c and fibrosis-score calculator helpers in `ct_dose.py`, and the experimental generic task-audit supervisor in `agents/`. These are not substitutes for validated clinical decision support.

Optional legacy FastAPI/CLI service:

```bash
python cli.py serve --host 127.0.0.1 --port 8000
# Open http://127.0.0.1:8000/
python cli.py audit --task-id TASK-001 --primary 28.5
python cli.py verify-audit
```

The API has a demo task-audit endpoint at `/api/audit` and a deterministic mock chat response. Neither provides a validated radiology dose-quality review. The audit log is in memory; even with a persistent `AUDIT_SECRET_KEY` the records themselves do **not** survive process restarts. The regex-based identifier guard is incomplete and must not be used as a clinical de-identification solution.

## Tests

```bash
python -m pytest -q
python -m compileall -q ct_dose.py dose_metrics.py cli.py agents tests
node --check app.mjs
node --test dose.test.mjs
```

GitHub Actions runs Python 3.10–3.12 tests and Node tests. A separate Pages workflow publishes only the static worksheet files.

## Privacy and security

The browser application makes no network requests for examination data and uses no local storage. Follow the linked AAPM resources only if you wish to navigate to their sites. Do not input personal health information. CSV exports are escaped to reduce spreadsheet formula-injection risks; inspect files before importing into other tools.

For legacy server deployments, set a suitable `AUDIT_SECRET_KEY` server-side. Never put secrets in a browser app or checked-in files. The generic API is experimental and must be secured, assessed, and hosted appropriately before any production use.

## License

[MIT](LICENSE).
