# ClassroomIQ — Complete System Setup Guide

This guide covers setting up and running both the **Backend** (FastAPI + PostgreSQL) and the **Frontend** (React + TypeScript + Vite + Tailwind CSS) for ClassroomIQ.

---

## 📋 Prerequisites

Before starting, ensure you have the following installed on your machine:

- **Node.js**: v18.0.0+ (with `npm` v9.0.0+)
- **Python**: 3.10+
- **PostgreSQL**: 14+ running locally (default database: `tutor` or `classroomiq`)
- **Git**

---

## 🚀 Quick Start Summary

To run the complete system, open two terminal windows:

| Service | Directory | Command | Local URL |
|---|---|---|---|
| **Backend API** | `backend/` | `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` | http://localhost:8000 |
| **Frontend UI** | `frontend/` | `npm run dev` | http://localhost:5173 |

---

## 🎨 Frontend Setup Guide

### Step 1 — Navigate to the Frontend Directory

From the project root:

```bash
cd frontend
```

### Step 2 — Install Node Dependencies

Install all required frontend dependencies (React, Vite, TanStack Query, Zustand, Axios, Lucide Icons, Tailwind CSS, Framer Motion):

```bash
npm install
```

### Step 3 — Configure Environment Variables (Optional)

Create a `.env` or `.env.local` file inside `frontend/` if you need to override the API endpoint URL:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

> **Note**: If not specified, the API service defaults to connecting to `http://localhost:8000/api/v1`.

### Step 4 — Run the Frontend Development Server

Start the Vite development server:

```bash
npm run dev
```

Output:
```text
  VITE v6.1.0  ready in 250 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

Open your browser and navigate to: **[http://localhost:5173](http://localhost:5173)**

### Step 5 — Verify Production Build (Optional)

To verify that the frontend builds cleanly without TypeScript or bundler errors:

```bash
npm run build
```

To preview the production build locally:

```bash
npm run preview
```

---

## 🐍 Backend Setup Guide

### Step 1 — Navigate to the Backend Directory

From the project root:

```bash
cd backend
```

### Step 2 — Create the Python Virtual Environment

```powershell
python -m venv .venv
```

### Step 3 — Activate the Virtual Environment

- **Windows (PowerShell)**:
  ```powershell
  .\.venv\Scripts\activate
  ```
- **Windows (CMD)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **macOS / Linux**:
  ```bash
  source .venv/bin/activate
  ```

After activation, your prompt will display `(.venv)`.

### Step 4 — Install Dependencies

```powershell
pip install -r requirements.txt
```

### apart of project route
```powershell
pip install -r ..\requirements.txt
```


### Step 5 — Configure Environment Variables

Ensure `.env` exists at the project root (`ClassroomIQ/.env`):

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/classroomiq
```

### Step 6 — Run the Backend Server

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
### overall backend -
```cd backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```


---

## 🛠️ Project Structure Overview

```text
ClassroomIQ/
├── backend/                    ← FastAPI Application & Database Layer
│   ├── .venv/                  ← Python Virtual Environment
│   ├── app/                    ← Models, Services, Repositories, APIs
│   │   ├── api/                ← 13 REST Routers (Validation, Coverage, Teaching, etc.)
│   │   ├── models/             ← 34 Active SQLAlchemy ORM Models
│   │   ├── services/           ← Core Business & AI Intelligence Engines
│   │   └── main.py             ← FastAPI Entrypoint
│   └── requirements.txt        ← Backend Dependencies
│
├── frontend/                   ← React + TypeScript + Vite SPA
│   ├── node_modules/           ← Node Dependencies
│   ├── src/                    ← Components, Pages, State Services, UI Layouts
│   │   ├── components/         ← Reusable Components & Widgets
│   │   ├── pages/              ← Dashboard & Module Pages
│   │   ├── services/           ← API Client Services (Axios)
│   │   ├── store/              ← Global State (Zustand)
│   │   └── main.tsx            ← React Entrypoint
│   ├── package.json            ← Node Package Configuration
│   ├── vite.config.ts          ← Vite Bundler Config
│   └── tailwind.config.js      ← Tailwind CSS Styling Config
│
└── SETUP.md                    ← Setup Guide
```

---

## ❓ Troubleshooting & FAQs

| Issue | Cause | Fix |
|---|---|---|
| `npm run dev` fails with missing modules | Dependencies not installed | Run `npm install` inside the `frontend/` directory |
| API calls fail with CORS error | Backend CORS not configured | Ensure backend `app/main.py` permits `http://localhost:5173` |
| `ERR_CONNECTION_REFUSED` | Backend server not running | Start backend with `uvicorn app.main:app --reload` on port 8000 |
| `TypeScript error during build` | Unresolved types | Run `npx tsc --noEmit` to locate type mismatches |
