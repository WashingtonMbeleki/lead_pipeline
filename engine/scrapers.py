import time
import random
import requests
import apprise
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from data_pipeline.db import ApplicationDatabase


class NotificationManager:
    def __init__(self, ntfy_topic: str = "washie_job_leads"):
        self.apobj = apprise.Apprise()
        # Default: Free instant push alerts via ntfy.sh
        # You can download the ntfy app on phone or open https://ntfy.sh/washie_job_leads
        self.apobj.add(f"ntfy://{ntfy_topic}")

    def send_high_match_alert(self, title: str, company: str, location: str, match_score: float, job_url: str):
        subject = f"🔥 Hot Lead ({int(match_score * 100)}% Match): {title}"
        body = (
            f"Company: {company}\n"
            f"Location: {location}\n"
            f"Match Score: {match_score:.2f}\n\n"
            f"Apply Link: {job_url}"
        )
        try:
            self.apobj.notify(title=subject, body=body)
            print(f"[PUSH ALERT SENT] Notified for high-match role: {title} at {company}", flush=True)
        except Exception as err:
            print(f"[PUSH ALERT FAILED] Could not dispatch alert: {err}", flush=True)


class BaseScraper(ABC):
    def __init__(self, db: ApplicationDatabase):
        self.db = db

    @abstractmethod
    def fetch_jobs(self, keywords: str, location: str, pages: int, user_skills: List[str]) -> List[Dict[str, Any]]:
        pass


class LinkedInPublicAPIScraper(BaseScraper):
    def __init__(self, db: ApplicationDatabase, notifier: NotificationManager = None):
        super().__init__(db)
        self.notifier = notifier or NotificationManager()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def calculate_match_score(self, title: str, user_skills: List[str]) -> Tuple[float, List[str]]:
        if not user_skills:
            return 0.75, []
        
        title_lower = title.lower()
        matched_skills = [skill for skill in user_skills if skill.lower() in title_lower]
        
        try:
            vectorizer = TfidfVectorizer()
            resume_doc = " ".join(user_skills)
            matrix = vectorizer.fit_transform([resume_doc, title])
            semantic_score = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
        except Exception:
            semantic_score = 0.0

        keyword_score = 0.70 + (len(matched_skills) * 0.08)
        combined_score = (keyword_score * 0.7) + (semantic_score * 0.3) + 0.1
        return min(combined_score, 0.98), matched_skills

    def fetch_page_with_retry(self, url: str, max_retries: int = 3) -> requests.Response | None:
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    return response
                
                if response.status_code == 429:
                    wait_time = (attempt * 3) + random.uniform(1.5, 3.5)
                    print(f"[RATE LIMITED 429] Retrying in {wait_time:.1f}s (Attempt {attempt}/{max_retries})", flush=True)
                    time.sleep(wait_time)
                else:
                    return None
            except Exception:
                time.sleep(2)
        return None

    def fetch_jobs(
        self, 
        keywords: str = "Software Engineer", 
        location: str = "South Africa", 
        pages: int = 3,
        user_skills: List[str] = None
    ) -> List[Dict[str, Any]]:
        user_skills = user_skills or []
        discovered_jobs = []
        formatted_keywords = keywords.replace(" ", "%20")
        formatted_location = location.replace(" ", "%20")

        for page in range(pages):
            start = page * 25
            api_url = (
                f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
                f"?keywords={formatted_keywords}&location={formatted_location}&start={start}"
            )

            print(f"Fetching page {page + 1}/{pages} (start={start}) from: {api_url}", flush=True)

            response = self._fetch_page_with_retry(api_url)
            if not response or response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            job_cards = soup.find_all("li")

            if not job_cards:
                print(f"[INFO] Reached end of feed at page {page + 1}.", flush=True)
                break

            for index, card in enumerate(job_cards):
                try:
                    title_elem = card.find("h3", class_="base-search-card__title")
                    company_elem = card.find("h4", class_="base-search-card__subtitle")
                    location_elem = card.find("span", class_="job-search-card__location")
                    link_elem = card.find("a", class_="base-card__full-link")

                    if not title_elem or not link_elem:
                        continue

                    job_title = title_elem.text.strip()
                    company_name = company_elem.text.strip() if company_elem else "Unknown Company"
                    job_location = location_elem.text.strip() if location_elem else location
                    job_url = link_elem["href"].split("?")[0]
                    job_id = f"li_pub_{int(time.time())}_{page}_{index}"

                    match_score, matched_skills = self._calculate_match_score(job_title, user_skills)
                    matched_str = ", ".join(matched_skills) if matched_skills else "General Profile Alignment"

                    job_data = {
                        "job_id": job_id,
                        "platform": "LinkedIn Public Feed",
                        "title": job_title,
                        "company": company_name,
                        "location": job_location,
                        "job_url": job_url
                    }

                    self.db.log_job(job_data)
                    self.db.record_application(
                        job_id=job_id,
                        status="DISCOVERED",
                        failure_reason=matched_str,
                        match_score=match_score
                    )

                    # Trigger push notification if match score is >= 0.88
                    if match_score >= 0.88:
                        self.notifier.send_high_match_alert(
                            title=job_title,
                            company=company_name,
                            location=job_location,
                            match_score=match_score,
                            job_url=job_url
                        )

                    discovered_jobs.append(job_data)
                except Exception:
                    continue

            time.sleep(random.uniform(2.5, 4.5))

        return discovered_jobs