# CT Dose Tracker

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

CT Dose Tracker (CTDI/DLP) tracks CTDIvol, DLP and effective dose per scan, flags ACR Pass/Fail and cumulative dose. Includes clinical calculation modules for MELD-Na, QTc, BMI, HbA1c, APRI/FIB-4 scores.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Clinical Calculation Functions

- **`calculate_meld_na()`** — MELD-Na score for liver disease severity assessment
- **`calculate_qtc()`** — QTc (corrected QT interval) using Bazett's formula
- **`calculate_bmi_z()`** — BMI calculation with pediatric/adult support
- **`convert_hba1c()`** — Convert between HbA1c (%) and estimated average glucose (mg/dL)
- **`calculate_apri_fib4()`** — APRI and FIB-4 scores for liver fibrosis assessment
- **`calculate_score()`** — Generic weighted scoring formula
- **`assess_row()`** — Auto-detects input type and routes to appropriate calculator
- **`process_csv()`** — Batch processing of CSV files with path traversal protection

### 🛡️ Security & Enterprise Architecture

- **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers
- **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation
- **Path Traversal Protection:** File operations validated to prevent directory escape
- **Secure Defaults:** Audit keys generated via `secrets.token_hex()` if not configured externally

### 🌐 API & Telemetry

- **FastAPI REST API:** OpenAPI 3.1 endpoints for audit, chat, and metrics
- **Prometheus Metrics:** Operational metrics at `/metrics`
- **WebSocket Telemetry:** Real-time event streaming

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/ct-dose-tracker.git
cd ct-dose-tracker

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🚀 Usage

### CLI Commands

```bash
# Run single task evaluation
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2

# Batch process CSV records
python cli.py batch -i input.csv -o results.csv

# Verify HMAC audit trail integrity
python cli.py verify-audit

# Launch FastAPI REST server
python cli.py serve --host 127.0.0.1 --port 8000
```

### Direct Clinical Calculations

```python
import ct_dose

# MELD-Na score
result = ct_dose.calculate_meld_na(bilirubin=2.0, creatinine=1.5, inr=1.2)
print(result)  # {'meld_na': 15.2, 'risk': 'MODERATE'}

# QTc calculation
result = ct_dose.calculate_qtc(qt_ms=400, hr_bpm=60)
print(result)  # {'qtc_ms': 400.0, 'prolonged': False}

# Auto-detect calculation type
result = ct_dose.assess_row({'bilirubin': 2.0, 'creatinine': 1.5})
```

### Batch CSV Processing

```bash
python ct_dose.py single --json '{"bilirubin": 2.0, "creatinine": 1.5}'
python ct_dose.py batch --input sample.csv --output results.csv
```

---

## 🧪 Testing

```bash
# Run full test suite
pytest -v

# Run with coverage
pytest -v --cov=.

# Run specific test module
pytest tests/test_ct_dose_calculations.py -v
```

---

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or manually
docker build -t ct-dose-tracker .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key ct-dose-tracker
```

---

## 🔧 Configuration

| Environment Variable | Description | Default |
|:---------------------|:------------|:--------|
| `AUDIT_SECRET_KEY` | HMAC-SHA256 key for audit trail signing | Random (session-scoped) |
| `MODEL_PROVIDER` | LLM provider (`mock`, `ollama`, `claude`, `openai`) | `mock` |

> **Security Note:** Always set `AUDIT_SECRET_KEY` in production to ensure audit trail persistence across restarts.

---

## 📁 Project Structure

```
ct-dose-tracker/
├── agents/              # Enterprise agent framework
│   ├── base.py          # Security, PHI guard, audit trail
│   ├── models.py        # Pydantic data models
│   ├── supervisor.py    # Multi-agent orchestrator
│   ├── workers.py       # Specialized domain workers
│   ├── api.py           # FastAPI REST endpoints
│   ├── llm_factory.py   # LLM provider factory
│   ├── learning.py      # Bayesian calibration engine
│   ├── metrics.py       # Prometheus metrics collector
│   └── streamer.py      # WebSocket telemetry
├── tests/               # Pytest test suite
├── web/                 # Operations console (HTML)
├── ct_dose.py           # Core clinical calculations
├── cli.py               # Command-line interface
├── enrichment.py        # Domain enrichment engines
├── simulator.py         # High-throughput stress testing
├── requirements.txt     # Python dependencies
├── Dockerfile           # Container build
└── docker-compose.yml   # Container orchestration
```

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.
