import os
import json
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from data_pipeline.scraper import JobScraper
from data_pipeline.db import ApplicationDatabase
from engine.cv_generator import TailoredCVGenerator

def load_master_skills(profile_path: str = "data/master_profile.json") -> List[str]:
    """Loads all technical skills directly from master_profile.json."""
    skills: List[str] = []
    if os.path.exists(profile_path):
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                categories = data.get("skill_categories", {})
                for skill_list in categories.values():
                    if isinstance(skill_list, list):
                        skills.extend(skill_list)
        except Exception as err:
            print(f"[ERROR] Failed to load master profile: {err}")
    return skills

def calculate_match_score(job_desc: str, profile_skills: List[str]) -> tuple[float, str]:
    """Calculates TF-IDF cosine similarity score and extracts key matched terms."""
    if not profile_skills or not job_desc:
        return 0.50, "General Profile Alignment"

    profile_text = " ".join(profile_skills)
    documents = [profile_text, job_desc]

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(documents)
    
    score = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
    
    # Scale score slightly for realistic match representation
    scaled_score = min(round(0.60 + (score * 0.40), 2), 0.98)

    # Extract overlapping words as matched keywords
    feature_names = vectorizer.get_feature_names_out()
    profile_words = set(profile_text.lower().split())
    matched_words = [word for word in feature_names if word in profile_words and word in job_desc.lower()]
    matched_str = ", ".join(matched_words[:6]) if matched_words else ", ".join(profile_skills[:5])

    return scaled_score, matched_str

def run_pipeline() -> None:
    """Executes the end-to-end ingestion, scoring, and auto-CV generation workflow."""
    print("🚀 Starting Job Application Pipeline...")

    db = ApplicationDatabase("data/job_applications.db")
    scraper = JobScraper()
    cv_gen = TailoredCVGenerator()

    # 1. Load Master Profile Skills
    profile_skills = load_master_skills()
    print(f"📦 Loaded {len(profile_skills)} target skills from master_profile.json")

    # 2. Scrape Jobs (Graduate, Intern, Trainee & Core Engineering roles)
    print("🔍 Scraping public job listings...")
    jobs: List[Dict[str, Any]] = scraper.scrape_linkedin_jobs(location="South Africa")
    print(f"✅ Found {len(jobs)} total listings.")

    # 3. Process, Score, and Ingest into SQLite
    ingested_count = 0
    generated_cv_count = 0

    for job in jobs:
        score, matched_keywords = calculate_match_score(job["description"], profile_skills)

        # Generate a unique job ID based on company + title
        job_id = f"{job['company']}_{job['title']}".lower().replace(" ", "_")
        job_id = "".join(c for c in job_id if c.isalnum() or c == "_")

        # Save to SQLite database
        db.save_job(
            job_id=job_id,
            title=job["title"],
            company=job["company"],
            location=job["location"],
            job_url=job["job_url"],
            description=job["description"]
        )

        db.save_application(
            job_id=job_id,
            match_score=score,
            status="DISCOVERED",
            failure_reason=matched_keywords
        )
        ingested_count += 1

        # Automatically pre-generate tailored CVs for high-matching leads (>= 75%)
        if score >= 0.75:
            skills_list = [s.strip() for s in matched_keywords.split(",") if s.strip()]
            cv_gen.generate_cv_pdf(
                job_title=job["title"],
                company=job["company"],
                matched_skills=skills_list,
                job_description=job["description"]
            )
            generated_cv_count += 1

    print(f"🎉 Pipeline run complete!")
    print(f"   - Total Ingested Jobs: {ingested_count}")
    print(f"   - Auto-Generated Tailored CVs (Score >= 0.75): {generated_cv_count}")

if __name__ == "__main__":
    run_pipeline()