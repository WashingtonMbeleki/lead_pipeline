import os
import json
import re
from typing import Any, Dict, List, cast
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa  # type: ignore

class TailoredCVGenerator:
    def __init__(self, master_cv_path: str = "data/master_profile.json", template_dir: str = "templates") -> None:
        self.master_cv_path: str = master_cv_path
        self.template_dir: str = template_dir
        self.master_data: Dict[str, Any] = {}
        os.makedirs("data/generated_cvs", exist_ok=True)
        self.reload_master_data()

    def reload_master_data(self) -> None:
        """Reloads master JSON file on demand to catch profile updates without restarting."""
        if os.path.exists(self.master_cv_path):
            try:
                with open(self.master_cv_path, "r", encoding="utf-8") as f:
                    loaded_data: Any = json.load(f)
                    if isinstance(loaded_data, dict):
                        self.master_data = loaded_data
                    else:
                        self.master_data = {}
            except Exception as err:
                print(f"[ERROR] Could not parse master profile JSON: {err}", flush=True)
                self.master_data = {}
        else:
            self.master_data = {}

    def _analyze_job_requirements(self, job_title: str, job_description: str) -> Dict[str, Any]:
        """Analyzes the job title and posting text to extract core technical emphasis."""
        text = f"{job_title} {job_description}".lower()
        
        is_data = any(k in text for k in ["data", "etl", "pipeline", "sql", "warehouse", "analytics", "database"])
        is_backend = any(k in text for k in ["backend", "api", "rest", "microservice", "service", "python", "java", "node"])
        is_grad = any(k in text for k in ["graduate", "intern", "trainee", "junior", "entry"])

        if is_data:
            focus = "relational persistence, query optimization, ETL concepts, and data-backed backend services"
            theme = "Data Engineering & Systems Architecture"
        elif is_backend:
            focus = "REST API engineering, microservices, system persistence, and clean backend design"
            theme = "Backend Development & API Engineering"
        elif is_grad:
            focus = "rapid technical adaptability, test-driven development (TDD), object-oriented design, and collaborative software execution"
            theme = "Software Engineering Foundations & Growth"
        else:
            focus = "full-stack backend features, relational persistence, and workflow automation"
            theme = "Software & Data Engineering"

        return {
            "focus": focus,
            "theme": theme,
            "is_grad": is_grad,
            "is_data": is_data
        }

    def generate_cv_pdf(self, job_title: str, company: str, matched_skills: List[str], job_description: str = "") -> str:
        """Renders the master profile using the Jinja2 HTML layout and exports an ATS-compliant PDF."""
        self.reload_master_data()
        
        full_name = self.master_data.get("full_name", "WASHINGTON MBELEKI")
        skills_str = ", ".join(matched_skills[:8]) if matched_skills else "Python, SQL, REST APIs, and Relational Storage"
        
        # Deep Job Analysis
        analysis = self._analyze_job_requirements(job_title, job_description)

        # 1. Custom Page 1 Profile
        tailored_summary = (
            f"Software engineer targeting the {job_title} position at {company}. "
            f"Brings practical experience in building backend services, API integrations, and relational persistence layers. "
            f"Direct technical alignment for this role includes {skills_str}. Proven track record in {analysis['focus']}, "
            f"supported by award-winning hackathon achievements and academic peer tutoring at WeThinkCode_."
        )

        # 2. Custom Page 1 Role-Fit Summary
        role_fit_summary = (
            f"Role-Fit Summary ({job_title} @ {company}): Key matching strengths include practical competence in "
            f"{skills_str}, test-driven development (TDD), and relational persistence. Demonstrates immediate engineering value for "
            f"{company}'s development goals with an ongoing commitment to mastering scalable data pipeline architectures."
        )

        default_skills: Dict[str, List[str]] = {
            "Languages & query": ["Python", "SQL", "Java", "JavaScript", "TypeScript", "Bash/Shell"],
            "Data & storage": ["SQLite", "Cloudflare D1", "Cloudflare KV", "Relational data storage", "Persistence", "Caching", "ETL concepts"],
            "Backend & integration": ["REST APIs", "Flask", "Node.js", "Hono", "Cloudflare Workers", "Microservices", "JWT", "Third-party API integration"],
            "Workflow & engineering": ["Workflow automation", "TDD", "JUnit 5", "Object-oriented design", "Git/GitHub", "GitLab CI/CD", "Linux", "Docker", "Maven", "Agile"]
        }

        raw_skills: Any = self.master_data.get("skill_categories")
        skill_categories = cast(Dict[str, List[str]], raw_skills) if isinstance(raw_skills, dict) else default_skills

        # 3. Dynamic Proof Points Prioritization for Page 2
        all_proof_points = self.master_data.get("proof_points", [])
        if analysis['is_data']:
            # Prioritize pipeline, persistence, and database projects
            prioritized_proofs = sorted(
                all_proof_points,
                key=lambda x: 0 if ("ETL" in x.get("demonstrates", "") or "pipeline" in x.get("demonstrates", "").lower() or "storage" in x.get("demonstrates", "").lower()) else 1
            )
        else:
            prioritized_proofs = all_proof_points

        context: Dict[str, Any] = {
            "full_name": full_name,
            "title": self.master_data.get("title", "SOFTWARE ENGINEER | DATA ENGINEER"),
            "contact": self.master_data.get("contact", {
                "location": "Johannesburg, South Africa",
                "email": "washiembeleki2003@gmail.com",
                "phone": "084 496 9910",
                "github": "github.com/WashingtonMbeleki",
                "linkedin": "linkedin.com/in/washie"
            }),
            "tailored_summary": tailored_summary,
            "role_fit_summary": role_fit_summary,
            "skill_categories": skill_categories,
            "experiences": self.master_data.get("experiences", []),
            "projects": self.master_data.get("projects", []),
            "education": self.master_data.get("education", {}),
            "certifications": self.master_data.get("certifications", []),
            "proof_points": prioritized_proofs,
            "gaps_and_plan": self.master_data.get("gaps_and_plan", []),
            "first_90_days": self.master_data.get("first_90_days", [])
        }

        env = Environment(loader=FileSystemLoader(self.template_dir))
        template = env.get_template("cv_template.html")
        rendered_html = template.render(context)

        # File Naming Standard: Name-Surname-Role-CV.pdf
        name_parts = full_name.title().split()
        first_name = name_parts[0] if name_parts else "Washington"
        last_name = name_parts[-1] if len(name_parts) > 1 else "Mbeleki"

        sanitized_title = job_title.replace("C#", "CSharp").replace("c#", "CSharp")
        clean_role = re.sub(r'[^a-zA-Z0-9]', '-', sanitized_title)
        clean_role = re.sub(r'-+', '-', clean_role).strip('-')

        pdf_filename = f"data/generated_cvs/{first_name}-{last_name}-{clean_role}-CV.pdf"

        with open(pdf_filename, "wb") as pdf_file:
            _ = pisa.CreatePDF(rendered_html, dest=pdf_file)  # type: ignore[no-untyped-call]

        print(f"[CV GENERATED] Tailored PDF saved for '{job_title}' at {company}: {pdf_filename}", flush=True)
        return pdf_filename