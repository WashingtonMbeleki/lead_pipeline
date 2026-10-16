WTC-8NWP9SCA


# Assisted Job Application & Dynamic CV Engine
An automated, human-in-the-loop job application pipeline built for software and data engineering roles. The system scrapes public job boards (targeting Graduate, Intern, Trainee, and Junior positions), scores listings using TF-IDF semantic matching against a centralized Master Profile, and dynamically generates job-tailored, multi-page PDF CVs and Strategic Briefs.

## Project Structure
lead_pipeline/
├── data/
│   ├── master_profile.json          # Single source of truth for profile, skills, & projects
│   ├── job_applications.db          # SQLite relational database
│   └── generated_cvs/               # Output folder for custom tailored PDF resumes
├── data_pipeline/
│   ├── scraper.py                   # Public job board scraper
│   └── db.py                        # SQLite database management & migrations
├── engine/
│   └── cv_generator.py              # Dynamic job analysis & multi-page PDF compilation engine
├── dashboard/
│   └── app.py                       # Streamlit interactive application feed & analytics
├── templates/
│   └── cv_template.html             # Multi-page HTML/CSS template for xhtml2pdf
├── docs/                            # Supporting documentation & specs
├── main.py                          # End-to-end CLI execution script
└── README.md

#### Database Schema & Entity-Relationship Diagram (ERD)
```bash
The application uses SQLite (data/job_applications.db) for lightweight local persistence. Below is the relational schema design.

Entity-Relationship Diagram (ERD)
```
┌─────────────────────────────┐             ┌──────────────────────────────────┐
│            jobs             │             │           applications           │
├─────────────────────────────┤             ├──────────────────────────────────┤
│ PK  job_id          TEXT    │◄── 1 : 1 ───│ PK  job_id          TEXT (FK)    │
│     title           TEXT    │             │     match_score     REAL         │
│     company         TEXT    │             │     status          TEXT         │
│     location        TEXT    │             │     failure_reason  TEXT         │
│     job_url         TEXT    │             │     updated_at      TIMESTAMP    │
│     description     TEXT    │             └──────────────────────────────────┘
│     created_at      TIMESTAMP│
└─────────────────────────────┘

```bash
    Table Definitions

    1.jobs_Table: Stores scraped listing details.
        job_id: Primary Key (slugified combination of company and title)
        title: Job position title
        company: Hiring organization
        location: Job location (e.g., Johannesburg, South Africa)
        job_url: Direct outbound link to the posting
        description: Full scraped text used for NLP matching
        created_at: Timestamp of initial scraping

    2.applications_Table: Tracks candidate workflow state per job lead.
        job_id: Foreign Key referencing jobs(job_id)
        match_score: Calculated TF-IDF cosine similarity score
        status: Current application state (DISCOVERED, APPLIED, REJECTED)
        failure_reason: Extracted keywords matching between profile and description
        updated_at: Last modification timestamp
```



##### Database Schema & Entity-Relationship Diagram (ERD)
    #Step 1: Clone and Setup Virtual Environment
        git clone https://github.com/WashingtonMbeleki/lead_pipeline.git
        cd lead_pipeline
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt

    #Step 2: Run Pipeline Ingestion
        python main.py
    
    #Step 3: Launch Streamlit Dashboard
        streamlit run dashboard/app.py