# Backend Setup Guide

This guide covers setting up the Python virtual environment and running the backend for ClassroomIQ.

---

## Prerequisites

- Python 3.10+ installed
- PostgreSQL running locally (port 5555 as configured)
- Git

---

## Step 1 — Clone the Repository

```bash
git clone https://github.com/pujareddy2/ClassroomIQ.git
cd ClassroomIQ
```

---

## Step 2 — Create the Virtual Environment

Navigate into the `backend/` directory and create a virtual environment:

```powershell
cd backend
python -m venv .venv
```

> This creates an isolated Python environment inside `backend/.venv/`

---

## Step 3 — Activate the Virtual Environment

### On Windows (PowerShell):
```powershell
.\.venv\Scripts\activate
```

### On Windows (Command Prompt):
```cmd
.venv\Scripts\activate.bat
```

### On macOS / Linux:
```bash
source .venv/bin/activate
```

After activation, your terminal prompt will show `(.venv)` at the beginning.

---

## Step 4 — Install Dependencies

```powershell
pip install -r requirements.txt
```

This installs all pinned packages including FastAPI, SQLAlchemy, Alembic, psycopg2, etc.

---

## Step 5 — Configure Environment Variables

Create a `.env` file at the **project root** (`ClassroomIQ/.env`):

```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/tutor
```

> ⚠️ Replace `yourpassword` and port number with your actual PostgreSQL credentials.
> The project is pre-configured to use port `5555`.

---

## Step 6 — Initialize the Database

Run the database initialization script to create all 19 tables:

```powershell
python ..\scratch\init_db.py
```

Or from the project root:
```powershell
& "backend\.venv\Scripts\python.exe" scratch\init_db.py
```

---

## Step 7 — Run the FastAPI Server

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Project Structure (Backend)

```
backend/
├── .venv/                      ← Virtual environment (DO NOT commit)
├── requirements.txt            ← Pinned dependencies
├── .env                        ← Environment config (DO NOT commit)
│
└── app/
    ├── main.py                 ← FastAPI app entrypoint
    │
    ├── db/
    │   ├── base_class.py       ← SQLAlchemy DeclarativeBase
    │   ├── base.py             ← Imports Base + all models (for Alembic)
    │   ├── database.py         ← Engine configuration
    │   └── session.py          ← SessionLocal + get_db() dependency
    │
    └── models/
        ├── __init__.py
        ├── institution.py
        ├── user.py
        ├── department.py
        ├── faculty.py
        ├── course.py
        ├── academic_term.py
        ├── curriculum.py
        ├── topic.py
        ├── reference_material.py
        ├── topic_reference.py
        ├── lecture_session.py
        ├── recording.py
        ├── transcript.py
        ├── transcript_segment.py
        ├── coverage_report.py
        ├── validation_flag.py
        ├── review_decision.py
        ├── recommendation.py
        └── report.py
```

---

## Deactivate Virtual Environment

When done working:

```powershell
deactivate
```

---

## Common Errors & Fixes

| Error | Fix |
|---|---|
| `pip install requirements.txt` fails | Use `pip install -r requirements.txt` (note the `-r` flag) |
| `DATABASE_URL not set` | Make sure `ClassroomIQ/.env` exists with correct URL |
| `No module named 'app'` | Run commands from inside the `backend/` directory |
| `venv\Scripts\activate` not found | Make sure you ran `python -m venv .venv` first |
