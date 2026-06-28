# 🏀 Pick-Up Hoops

A local multi-service application for coordinating pick-up basketball games. Built with FastAPI, SQLModel, Streamlit, Redis, and Docker Compose.

---

## Project Overview

| Exercise | Focus | Status |
|---|---|---|
| EX1 | FastAPI CRUD backend + SQLite persistence + tests | ✅ Done |
| EX2 | Streamlit dashboard UI talking to the API | ✅ Done |
| EX3 | Multi-service stack with Docker Compose, async worker, JWT security, and runbook | ✅ Done |

EX3 documentation and architecture notes: [docs/EX3-notes.md](docs/EX3-notes.md)  
Compose runbook and enhancement walkthrough: [docs/runbooks/compose.md](docs/runbooks/compose.md)  
Demo entry point: [scripts/demo.sh](scripts/demo.sh)

---

## Tech Stack

- **Python 3.12** (managed with `uv`)
- **FastAPI** — REST API layer with JWT authentication and RBAC
- **SQLModel + SQLite** — ORM and local database
- **Streamlit** — interactive web dashboard
- **Redis** — async worker coordination and idempotency tracking
- **httpx + tenacity** — async HTTP client with retry logic
- **Docker Compose** — orchestrates the full four-service stack
- **Pytest** — automated testing

---

## Running the Full Stack (EX3)

The full stack runs four services via Docker Compose: the API, the Streamlit UI, Redis, and the background worker.

**1. Start everything**
```bash
bash scripts/demo.sh
```
or manually:
```bash
docker compose up --build
```

**2. Open the services**

| Service | URL |
|---|---|
| API (Swagger docs) | http://localhost:8000/docs |
| Streamlit dashboard | http://localhost:8501 |

**3. Seed sample data** (optional, first run only)
```bash
docker compose exec api python -m scripts.seed
```

> ⚠️ `database.db` is not committed to version control. It is auto-generated on first run.

---

## Running Without Docker (EX1 / EX2 mode)

**1. Install dependencies**
```bash
uv sync
```

**2. Start the API server** (Terminal 1)
```bash
uvicorn api.main:app --reload
```

**3. Start the Streamlit dashboard** (Terminal 2)
```bash
streamlit run dashboard.py
```

> ⚠️ The API must be running before opening the dashboard.

---

## Dashboard Features

**Authentication:** Login via the sidebar using a seeded admin or user account. Admin credentials are required for delete operations.

**Core flows:**
- **Courts** — add, update, and delete basketball courts (delete requires admin)
- **Players** — manage players and their skill levels
- **Games** — schedule games, update status, delete (admin only), and register players

**League Overview metrics** (top of dashboard):
- Total courts, registered players, and scheduled games

**Upcoming Games table** — filtered view of `open` games scheduled in the future, showing court, date, time, skill level, and live occupancy

**Enhancement — CSV Export:** The Upcoming Games table includes an **Export Games to CSV** button that downloads the current view as `games_schedule.csv`

---

## Background Worker

`scripts/refresh.py` is an async worker that runs on startup and marks past `open` games as `completed`. It uses:
- `asyncio.Semaphore` for bounded concurrency
- `tenacity` for automatic retries on transient failures
- Redis for idempotency — each game is processed at most once

---

## Running Tests

Tests use an in-memory SQLite database — no setup required.

```bash
uv run python -m pytest tests/
```

The test suite covers:
- Court CRUD (create, read, update, delete)
- JWT authentication (valid token, expired token, missing token, wrong role)
- Async worker logic (game filtering, idempotency, Redis deduplication)
- CSV export format

---

## Project Structure

```
.
├── api/
│   ├── main.py          # FastAPI app and route definitions
│   ├── models.py        # SQLModel entities + request/response schemas
│   ├── database.py      # DB engine and session management
│   └── auth.py          # JWT auth, password hashing, RBAC
├── scripts/
│   ├── refresh.py       # Async background worker (Redis-backed)
│   ├── seed.py          # Sample data seeder
│   └── demo.sh          # Demo entry point for graders
├── tests/
│   ├── test_api.py      # API and auth tests
│   └── test_refresh.py  # Async worker tests
├── docs/
│   ├── EX3-notes.md     # Architecture notes, security baseline, worker trace
│   └── runbooks/
│       └── compose.md   # Compose runbook and enhancement walkthrough
├── dashboard.py         # Streamlit dashboard
├── compose.yaml         # Docker Compose service definitions
└── pyproject.toml       # Project metadata and dependencies
```

---

## AI Assistance

A three-stage AI-assisted workflow was used throughout this project:

1. **Gemini** — brainstorming features, planning architecture, and drafting prompts
2. **GitHub Copilot** — wrote code based on those prompts across all three exercises
3. **Claude** — reviewed generated code and identified issues at each stage, including pagination bugs, stale session state, PATCH schema mismatches, missing auth guards, hardcoded secrets, and gaps in test coverage against the EX3 requirements