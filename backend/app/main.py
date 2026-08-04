from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.curriculum import router as curriculum_router
from app.api.reference_material import router as reference_router
from app.db import base  # noqa: F401 — imports all models so metadata is populated

app = FastAPI(
    title="ClassroomIQ — Academic Intelligence API",
    description=(
        "Backend API for the CITQ Academic Intelligence & Analytics Engine. "
        "Handles curriculum intelligence, RAG pipeline, technical validation, "
        "coverage analysis, teaching intelligence, and faculty recommendations."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Health Check ───────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "ClassroomIQ API is running"}


@app.get("/health", tags=["Health"])
def health_check():
    """Liveness probe — returns 200 if the API process is alive."""
    return {"status": "healthy"}


app.include_router(auth_router)
app.include_router(curriculum_router)
app.include_router(reference_router)
