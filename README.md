# 🛡️ Automated Data Quality Sentinel

An automated, defensive platform engineering pipeline designed to validate, sanitize, and quarantine transactional data streams in real-time. Built with **Great Expectations v1.x**, **SQLite**, **Pytest**, **GitHub Actions**, and **Streamlit**.

---

## 🎯 Problem Statement

In modern financial and platform data pipelines, silent data corruption is a severe operational risk. Upstream API breaking changes, missing payload attributes, incorrect currency labels, or improper VAT calculations routinely trickle down into warehouses and analytics layers, causing:

* **Inaccurate Financial Reporting:** Flawed transactional figures corrupting accounting balances and executive reporting.
* **Pipeline Failures:** Unhandled bad payloads breaking downstream transformation engines and jobs.
* **Compliance & Audit Blindspots:** Inability to track, log, and inspect why specific records were dropped or skipped.

### The Solution

The **Data Quality Sentinel** implements a **Defensive Quality Routing Pattern**:
1. Ingests raw batch payloads (South African ZAR transactional logs).
2. Runs explicit expectation suites using **Great Expectations v1.x**.
3. **Branches Payload Execution:**
   * **Clean Records** land directly in the production **SQLite Data Warehouse**.
   * **Corrupted/Invalid Records** are isolated into a structured **Dead-Letter Queue (`logs/dead_letter_queue.json`)** with diagnostic logs for developer inspection without stopping pipeline execution.
4. Provides live operational visibility via a **Streamlit Monitoring Dashboard**.

---

## 🏗️ Architecture & Pipeline Flow

```text
       ┌───────────────────────────────┐
       │ Raw Financial CSV Ingestion   │
       │ (South African Transactional) │
       └──────────────┬────────────────┘
                      │
                      ▼
       ┌───────────────────────────────┐
       │ Great Expectations Validation │
       │ (Schema, Enum, VAT & Amounts) │
       └──────────────┬────────────────┘
                      │
           ┌──────────┴──────────┐
           │                     │
    [ Clean Records ]    [ Invalid Records ]
           │                     │
           ▼                     ▼
┌─────────────────────┐ ┌─────────────────────────┐
│  SQLite Warehouse   │ │ Dead-Letter Queue (DLQ) │
│ (financial_wh.db)   │ │ (dead_letter_queue.json)│
└──────────┬──────────┘ └──────────┬──────────────┘
           │                       │
           └───────────┬───────────┘
                       │
                       ▼
         ┌───────────────────────────┐
         │ Streamlit Operational App │
         │   (Live Monitoring UI)    │
         └───────────────────────────┘
```

---

## 🛠️ Zero-Cost Tech Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Language** | Python 3.11+ | Core scripting, pipeline execution, and data routing |
| **Validation Engine** | Great Expectations v1.x | Data contract validation and schema assertion |
| **Storage / Warehouse** | SQLite 3 | Embedded, zero-cost SQL database |
| **Testing Engine** | Pytest | Automated integration testing for pipeline runs |
| **CI/CD Platform** | GitHub Actions | Automated build, test, and artifact uploading on code push |
| **Monitoring Dashboard** | Streamlit | Visual operational metrics for clean vs. quarantined data |

---

## 📋 Data Quality Specifications (Rules)

The pipeline enforces data assertions against South African financial log batches:

| Field | Data Type | Rule / Assertion | Action on Fail |
| :--- | :--- | :--- | :--- |
| `transaction_id` | String | Must be non-null string identifier (`TXN-ZA-XXXXX`) | Quarantine |
| `account_number` | String | Must be non-null 10-digit account identifier | Quarantine |
| `currency` | Enum | Must strictly equal **`ZAR`** | Quarantine |
| `amount` | Float | Must be positive numeric value (`amount > 0.00`) | Quarantine |
| `vat_amount` | Float | Must not exceed transaction amount (`vat <= amount`) | Quarantine |
| `status` | Enum | Allowed values: `['SUCCESS', 'FAILED', 'PENDING']` | Quarantine |
| `channel` | Enum | Allowed: `['POS', 'EFT', 'Capitec_Pay', 'CARD_ONLINE', 'ATM', 'RTC_EFT']` | Quarantine |

---

## 📂 Repository Directory Structure

```text
data-quality-sentinel/
├── .agents/                    # Agent environment skills
├── .claude/                    # Claude workspace skills
├── .github/
│   └── workflows/
│       └── sentinel_ci.yml     # GitHub Actions CI workflow definition
├── data/
│   ├── raw/
│   │   └── sa_financial_transactions.csv
│   └── processed/
│       └── financial_warehouse.db
├── docs/
│   └── data_dictionary.md
├── logs/
│   └── dead_letter_queue.json  # Quarantined invalid records with diagnostics
├── tests/
│   └── test_pipeline.py        # Pytest integration suite
├── app.py                      # Streamlit operational dashboard
├── generate_data.py            # Synthetic dataset generator with fault injection
├── validate_and_ingest.py      # Core GE v1.x validation & routing pipeline
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

---

## 🚀 Quick Start & Local Setup

### 1. Clone & Setup Environment
```bash
git clone https://github.com/YOUR_USERNAME/data-quality-sentinel.git
cd data-quality-sentinel

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Generate Synthetic Transaction Batch
Run the dataset generator script to produce sample South African transactional records with intentional data quality defects (~10% anomaly rate):
```bash
python generate_data.py
```

### 3. Run Pipeline Validation & Ingestion
Execute the validation and defensive routing pipeline:
```bash
python validate_and_ingest.py
```

### 4. Run Integration Tests
Execute the automated test suite using `pytest`:
```bash
python -m pytest tests/
```

### 5. Launch Operational Dashboard
Start the Streamlit dashboard to view clean database metrics alongside dead-letter queue diagnostics:
```bash
streamlit run app.py
```

---

## 🔄 CI/CD Automation (GitHub Actions)

Every code push or pull request to `main` triggers `.github/workflows/sentinel_ci.yml`:
1. Sets up Python 3.11 environment and restores pip cache.
2. Installs pinned dependencies from `requirements.txt`.
3. Executes `generate_data.py` and `validate_and_ingest.py`.
4. Runs `pytest` integration test suite.
5. **Uploads `dead_letter_queue.json` as a CI build artifact** for post-build failure analysis.