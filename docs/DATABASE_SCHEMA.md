# Database Schema & Entity-Relationship Diagram (ERD)

The application uses SQLite (`data/job_applications.db`) for lightweight local data storage.

## Entity-Relationship Diagram (ERD)

```text
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


