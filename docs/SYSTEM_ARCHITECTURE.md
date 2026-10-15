# System Architecture & Technical Specification

## Core Components
- **Single Source of Truth (`data/master_profile.json`)**: Contains biographical data, categorized skills, professional experience, projects, certifications, proof points, development gaps, and a 90-day roadmap. No static `resume.pdf` is required.
- **NLP Matching Engine (`main.py`)**: Uses scikit-learn's `TfidfVectorizer` and cosine similarity to evaluate profile alignment against job descriptions, outputting a match score and overlapping keyword list.
- **Dynamic PDF Renderer (`engine/cv_generator.py`)**: Built with Jinja2 and xhtml2pdf. It analyzes job requirements to customize your summary, prioritize relevant project proof points, and compile a 2-part document saved as `Name-Surname-Role-CV.pdf`.

## Pipeline Data Flow
1. **Scraping**: `scraper.py` queries public listings targeting Graduate, Intern, Trainee, and Junior roles across South Africa.
2. **Scoring & Ingestion**: `main.py` calculates semantic match scores and persists records into SQLite (`data/job_applications.db`).
3. **Interactive Review**: `dashboard/app.py` (Streamlit) provides a UI to filter leads, review match metrics, and trigger on-demand custom CV generation.