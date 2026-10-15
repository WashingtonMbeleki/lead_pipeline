import os
import re
from typing import Dict, List, Any
from pypdf import PdfReader

class ResumeParser:
    def __init__(self, pdf_path: str):
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Resume PDF not found at {pdf_path}")
        self.pdf_path = pdf_path
        self.raw_text = self._extract_text()

    def _extract_text(self) -> str:
        reader = PdfReader(self.pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    def parse_profile(self) -> Dict[str, Any]:
        """Extract key structural attributes from the raw CV text."""
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', self.raw_text)
        phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', self.raw_text)

        # Tech skill keyword matching
        common_skills = [
            "Python", "Java", "JavaScript", "TypeScript", "SQL", "React", 
            "Docker", "Git", "Linux", "REST API", "Data Engineering", "PySpark"
        ]
        extracted_skills = [skill for skill in common_skills if re.search(rf'\b{skill}\b', self.raw_text, re.I)]

        return {
            "email": email_match.group(0) if email_match else "",
            "phone": phone_match.group(0) if phone_match else "",
            "skills": extracted_skills,
            "raw_text": self.raw_text
        }

if __name__ == "__main__":
    # Quick sanity test
    print("ResumeParser module initialized.")