import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import get_current_user, router as auth_router
from app.api.coverage import router as coverage_router
from app.api.curriculum import router as curriculum_router
from app.api.explanations import router as explanations_router
from app.api.reference_material import router as reference_router
from app.api.transcript import router as transcript_router
from app.api.lecture import router as lecture_router
from app.api.validation import router as validation_router
from app.api.teaching import router as teaching_router
from app.api.recommendations import router as recommendations_router
from app.api.workflow import router as workflow_router
from app.api.analysis import router as analysis_router
from app.api.assistant import router as assistant_router
from app.api.rag import router as rag_router
from app.api.contract import install_api_contract
from app.db import base  # noqa: F401 — imports all models so metadata is populated
from app.db.init_db import init_db

app = FastAPI(
    title="ClassroomIQ — Academic Intelligence API",
    description=(
        "Backend API for the ClassroomIQ Academic Intelligence & Analytics Engine. "
        "Handles curriculum intelligence, RAG pipeline, technical validation, "
        "coverage analysis, teaching intelligence, faculty recommendations, "
        "and Explainable AI (XAI) trust layer."
    ),
    version="0.6.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

install_api_contract(app)

@app.on_event("startup")
def on_startup():
    init_db()

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",") if origin.strip()],
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


@app.get("/health/live", tags=["Health"])
def health_live():
    """Liveness probe — returns 200 if the API process is running."""
    return {"status": "alive"}


@app.get("/health/ready", tags=["Health"])
def health_ready():
    """Readiness probe — verifies database connectivity and core services."""
    try:
        from app.db.session import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            return {"status": "ready", "database": "connected"}
        finally:
            db.close()
    except Exception as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=f"Database not ready: {exc}")


app.include_router(auth_router, prefix="/api/v1")
_protected = [Depends(get_current_user)]
app.include_router(curriculum_router, prefix="/api/v1", dependencies=_protected)
app.include_router(reference_router, prefix="/api/v1", dependencies=_protected)
app.include_router(lecture_router, prefix="/api/v1", dependencies=_protected)
app.include_router(validation_router, prefix="/api/v1", dependencies=_protected)
app.include_router(coverage_router, prefix="/api/v1", dependencies=_protected)
app.include_router(teaching_router, prefix="/api/v1", dependencies=_protected)
app.include_router(recommendations_router, prefix="/api/v1", dependencies=_protected)
app.include_router(explanations_router, prefix="/api/v1", dependencies=_protected)
app.include_router(workflow_router, prefix="/api/v1", dependencies=_protected)
app.include_router(analysis_router, prefix="/api/v1", dependencies=_protected)
app.include_router(assistant_router, prefix="/api/v1", dependencies=_protected)
app.include_router(rag_router, prefix="/api/v1", dependencies=_protected)
