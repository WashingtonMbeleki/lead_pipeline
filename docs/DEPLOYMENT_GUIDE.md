### 3. `docs/DEPLOYMENT_GUIDE.md`
This document guides anyone (or yourself) through setting up dependencies and running the engine locally.

```markdown
# Deployment & Execution Guide

## Prerequisites
- Python 3.10+
- Virtual Environment (`venv`)

## Setup Instructions

**1. Clone Repository & Activate Environment**:
   ```bash
    git clone [https://github.com/WashingtonMbeleki/lead_pipeline.git](https://github.com/WashingtonMbeleki/lead_pipeline.git)
    cd lead_pipeline
    python3 -m venv venv
    source venv/bin/activate
   ```
**2.Install Dependencies:**
```bash
    pip install streamlit pandas plotly scikit-learn beautifulsoup4 requests jinja2 xhtml2pdf
```
**3.Run ingestion Piepline:**
```bash
    python main.py
```
**4.Launch Streamlit Dashboard:**
```bash
    streamlit run dashboard/app.py
```