import sqlite3
import os
from typing import Optional

class ApplicationDatabase:
    def __init__(self, db_path: str = "data/job_applications.db") -> None:
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Returns a connection to the SQLite database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Creates tables if they do not exist and runs column migrations."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Jobs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                job_url TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migration check: ensure description column exists if table was created previously
        cursor.execute("PRAGMA table_info(jobs)")
        columns = [column[1] for column in cursor.fetchall()]
        if "description" not in columns:
            cursor.execute("ALTER TABLE jobs ADD COLUMN description TEXT")

        # Applications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                job_id TEXT PRIMARY KEY,
                match_score REAL,
                status TEXT DEFAULT 'DISCOVERED',
                failure_reason TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES jobs (job_id)
            )
        """)

        conn.commit()
        conn.close()

    def save_job(self, job_id: str, title: str, company: str, location: str, job_url: str, description: str) -> None:
        """Inserts or replaces job listing records."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO jobs (job_id, title, company, location, job_url, description)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_id) DO UPDATE SET
                title=excluded.title,
                company=excluded.company,
                location=excluded.location,
                job_url=excluded.job_url,
                description=excluded.description
        """, (job_id, title, company, location, job_url, description))
        conn.commit()
        conn.close()

    def save_application(self, job_id: str, match_score: float, status: str = "DISCOVERED", failure_reason: Optional[str] = None) -> None:
        """Inserts application status and match score without overwriting existing status."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO applications (job_id, match_score, status, failure_reason)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(job_id) DO UPDATE SET
                match_score=excluded.match_score,
                failure_reason=excluded.failure_reason
        """, (job_id, match_score, status, failure_reason))
        conn.commit()
        conn.close()

    def update_application_status(self, job_id: str, status: str) -> None:
        """Updates status for a specific application."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE applications
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE job_id = ?
        """, (status, job_id))
        conn.commit()
        conn.close()