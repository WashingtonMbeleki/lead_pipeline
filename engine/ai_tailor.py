import json
import re
from typing import Any, Dict, List

class ProfileTailorEngine:
    def __init__(self, master_profile_path: str = "data/master_profile.json") -> None:
        self.master_profile_path = master_profile_path
        self.master_data: Dict[str, Any] = {}
        self.load_profile()

    def load_profile(self) -> None:
        try:
            with open(self.master_profile_path, "r", encoding="utf-8") as f:
                self.master_data = json.load(f)
        except Exception as err:
            print(f"[ERROR] Could not load master profile: {err}")

    def analyze_job_match(self, job_title: str, job_description: str) -> Dict[str, Any]:
        """Analyzes job description requirements against master profile skills."""
        jd_text = (job_title + " " + job_description).lower()
        
        all_skills: List[str] = []
        categories = self.master_data.get("skill_categories", {})
        for skill_list in categories.values():
            if isinstance(skill_list, list):
                all_skills.extend(skill_list) # type: ignore

        matched_skills = [skill for skill in all_skills if re.search(rf"\b{re.escape(skill.lower())}\b", jd_text)]
        if not matched_skills:
            matched_skills = ["Python", "SQL", "REST APIs", "Relational Databases"]

        # Dynamically tailor summary
        skills_str = ", ".join(matched_skills[:5])
        tailored_summary = (
            f"Software Engineer specializing in backend integration, relational data architectures, and data-backed applications, "
            f"targeting the {job_title} role. Direct technical alignment includes {skills_str}. "
            f"Demonstrated project record across persistent storage (SQLite, Cloudflare D1/KV), workflow automation, "
            f"API design, and operational data services, supported by clean code principles, TDD, and test-driven delivery."
        )

        # Dynamically tailor Role-Fit Summary
        role_fit_summary = (
            f"Role-Fit Alignment for {job_title}: Matches core requirements in {skills_str}. "
            f"Brings practical experience from projects like MoCredit (2nd Place MTN MoMo Hackathon) and Thuso Health, "
            f"demonstrating immediate value in API development, persistent transaction logging, and automated workflows."
        )

        return {
            "matched_skills": matched_skills,
            "tailored_summary": tailored_summary,
            "role_fit_summary": role_fit_summary
        }