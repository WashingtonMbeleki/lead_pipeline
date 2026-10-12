import os
import sys
import sqlite3
import json
import pytest

# Add project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from validate_and_ingest import run_pipeline, DB_PATH, DEAD_LETTER_PATH

def test_pipeline_execution():
    run_pipeline()
    
    assert os.path.exists(DB_PATH), "Database file was not created."
    assert os.path.exists(DEAD_LETTER_PATH), "Dead-letter log was not created."

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM transactions")
    count = cursor.fetchone()[0]
    conn.close()

    assert count > 0, "No records were inserted into the SQLite database."

    with open(DEAD_LETTER_PATH, "r") as f:
        dead_letter_data = json.load(f)
    
    assert isinstance(dead_letter_data, list), "Dead letter queue is not a valid list."