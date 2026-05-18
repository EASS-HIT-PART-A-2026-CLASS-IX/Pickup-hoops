# 🏀 Pick-Up Hoops

A local service for coordinating pick-up basketball games. Built with FastAPI, SQLModel, and Streamlit.

> **This is Part 2 of a multi-part project.** This part adds a Streamlit dashboard that communicates with the Part 1 FastAPI backend. Both services must be running simultaneously for the app to work.

---

## Project Overview

| Exercise | Focus | Status |
|---|---|---|
| EX1 | FastAPI CRUD backend + SQLite persistence + tests | ✅ Done |
| EX2 | Streamlit dashboard UI talking to the API | ✅ Done |
| EX3 | Multi-service stack with Docker Compose, persistence layer, async worker, security, and runbook | 🔜 Upcoming |

---

## Tech Stack

- **Python 3.12** (managed with `uv`)
- **FastAPI** — REST API layer
- **SQLModel + SQLite** — ORM and local database
- **Streamlit** — interactive web dashboard
- **Pytest** — automated testing

---

## Setup & Running

This project requires **two terminals running simultaneously** — one for the API, one for the dashboard.

**1. Install dependencies**
```bash
uv sync
```

**2. Start the API server** (Terminal 1)
```bash
uvicorn main:app --reload
```
The API will be available at `http://localhost:8000`.  
Interactive API docs (Swagger UI): `http://localhost:8000/docs`

**3. Start the Streamlit dashboard** (Terminal 2)
```bash
streamlit run dashboard.py
```
The dashboard will open automatically at `http://localhost:8501`.

> ⚠️ The API must be running before opening the dashboard. If the API is offline, the dashboard will show connection errors.

---

## Dashboard Features

**Core flows:**
- **Courts** — add, update, and delete basketball courts
- **Players** — manage players and their skill levels
- **Games** — schedule games, update status, delete, and register players

**Extra — League Overview metrics** (displayed at the top of the dashboard):
- Total courts registered
- Total registered players
- Total scheduled games

**Upcoming Games table** — filtered view showing only `open` games scheduled in the future, with court name, date, time, skill level, and live occupancy (`current / max players`)

Data is cached per session with a **🔄 Refresh Data** button to reload from the API after any external changes.

---

## Running Tests

Tests use an in-memory SQLite database — no setup required.

```bash
uv run python -m pytest
```

---

## Project Structure

```
.
├── main.py          # FastAPI app and all route definitions
├── models.py        # SQLModel entity definitions (Court, Player, Game)
├── database.py      # DB engine and session management
├── dashboard.py     # Streamlit dashboard (EX2)
├── pyproject.toml   # Project metadata and dependencies
└── database.db      # Auto-generated SQLite file (local only, not committed)
```

> ⚠️ `database.db` is not committed to version control. It is auto-generated on first run.

---

## AI Assistance

A three-stage AI-assisted workflow was used throughout this project:

1. **Gemini** — used for brainstorming ideas, planning features, and drafting the prompts sent to Copilot
2. **GitHub Copilot** — wrote the code based on those prompts (dashboard layout, API call patterns, form logic, session state structure)
3. **Claude** — used to review the generated code, identify issues, and suggest fixes — including pagination limits, stale session state after mutations, missing input validation, and datetime normalization in partial update logic

