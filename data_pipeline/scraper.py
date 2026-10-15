import time
import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any

class JobScraper:
    def __init__(self) -> None:
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        # Expanded target roles including Graduate, Trainee, and Intern
        self.target_roles = [
            "Data Engineer", 
            "Software Engineer", 
            "Junior Software Developer", 
            "Graduate Data Engineer", 
            "Graduate Developer", 
            "Software Engineering Trainee", 
            "Data Intern", 
            "Software Engineer Intern"
        ]

    def scrape_linkedin_jobs(self, location: str = "South Africa") -> List[Dict[str, Any]]:
        """Scrapes LinkedIn public job feeds targeting junior, graduate, trainee, and intern roles."""
        scraped_jobs: List[Dict[str, Any]] = []

        for role in self.target_roles:
            url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={role.replace(' ', '%20')}&location={location.replace(' ', '%20')}&start=0"
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                job_cards = soup.find_all("li")

                for card in job_cards:
                    title_elem = card.find("h3", class_="base-search-card__title")
                    company_elem = card.find("h4", class_="base-search-card__subtitle")
                    location_elem = card.find("span", class_="job-search-card__location")
                    link_elem = card.find("a", class_="base-card__full-link")

                    if title_elem and company_elem and link_elem:
                        job_title = title_elem.text.strip()
                        company = company_elem.text.strip()
                        job_location = location_elem.text.strip() if location_elem else location
                        job_url = link_elem["href"].split("?")[0] if "href" in link_elem.attrs else ""

                        scraped_jobs.append({
                            "title": job_title,
                            "company": company,
                            "location": job_location,
                            "job_url": job_url,
                            "description": f"{job_title} at {company}. Skills: Python, SQL, REST APIs, Databases, Git, ETL, Data Engineering."
                        })
                time.sleep(1)
            except Exception as err:
                print(f"[SCRAPER ERROR] Failed scraping for role '{role}': {err}")

        return scraped_jobs