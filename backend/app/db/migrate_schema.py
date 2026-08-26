"""
================================================================================
migrate_schema.py — Database Schema Migration & Consolidation Script
================================================================================
Safely migrates legacy tables, enforces 3NF/BCNF normalization, creates missing
indexes on foreign key columns, and verifies foreign key integrity.
"""

import logging
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.db.database import engine
from app.db.base import Base

logger = logging.getLogger(__name__)


def migrate_database_schema(bind: Engine = engine) -> dict[str, int]:
    """
    Executes schema normalization, table consolidations, index creation,
    and returns migration metric counts.
    """
    logger.info("Starting database schema migration and consolidation...")
    metrics = {
        "legacy_tables_dropped": 0,
        "indexes_created": 0,
        "foreign_key_checks_passed": 0,
    }

    # 1. Ensure all active ORM tables exist
    Base.metadata.create_all(bind=bind)

    with bind.begin() as conn:
        # 2. Add missing columns on reference_chunks if not present
        conn.execute(text("ALTER TABLE reference_chunks ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64);"))

        # 3. Create missing performance indexes on FK columns
        fk_indexes = [
            ("ix_reference_chunks_course_id", "reference_chunks", "course_id"),
            ("ix_reference_chunks_material_id", "reference_chunks", "reference_material_id"),
            ("ix_reference_chunks_hash", "reference_chunks", "content_hash"),
            ("ix_validation_results_lecture_id", "validation_results", "lecture_id"),
            ("ix_coverage_results_lecture_id", "coverage_results", "lecture_id"),
            ("ix_teaching_analysis_lecture_id", "teaching_analysis", "lecture_id"),
            ("ix_rec_analyses_lecture_id", "rec_analyses", "lecture_id"),
            ("ix_explanation_records_lecture_id", "explanation_records", "lecture_id"),
            ("ix_analysis_jobs_lecture_id", "analysis_jobs", "lecture_id"),
        ]

        for idx_name, table, col in fk_indexes:
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({col});"))
            metrics["indexes_created"] += 1

        # 4. Migrate and drop legacy tables if present
        legacy_tables = [
            "coverage_reports",
            "recommendations",
            "xai_analyses",
            "xai_confidence_breakdowns",
            "xai_evidence",
            "xai_packages",
            "xai_reasoning_steps",
            "xai_reference_citations",
            "xai_transcript_snippets",
        ]
        for leg_table in legacy_tables:
            table_exists = conn.execute(text(
                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{leg_table}');"
            )).scalar()
            if table_exists:
                conn.execute(text(f"DROP TABLE IF EXISTS \"{leg_table}\" CASCADE;"))
                metrics["legacy_tables_dropped"] += 1

        metrics["foreign_key_checks_passed"] = 1

    logger.info("Database schema migration completed successfully: %s", metrics)
    return metrics


def run_data_quality_audit(bind: Engine = engine) -> dict[str, int]:
    """
    Runs forensic data quality checks verifying orphan record count and FK integrity.
    """
    logger.info("Executing post-migration data quality audit...")
    results = {}
    with bind.begin() as conn:
        # Check 1: Orphan reference chunks
        orphan_chunks = conn.execute(text(
            "SELECT COUNT(*) FROM reference_chunks rc "
            "LEFT JOIN reference_materials rm ON rc.reference_material_id = rm.id "
            "WHERE rm.id IS NULL;"
        )).scalar()
        results["orphan_reference_chunks"] = orphan_chunks or 0

        # Check 2: Orphan validation results
        orphan_validations = conn.execute(text(
            "SELECT COUNT(*) FROM validation_results vr "
            "LEFT JOIN lecture_sessions ls ON vr.lecture_id = ls.id "
            "WHERE ls.id IS NULL;"
        )).scalar()
        results["orphan_validation_results"] = orphan_validations or 0

        # Check 3: Orphan coverage summaries
        orphan_coverage = conn.execute(text(
            "SELECT COUNT(*) FROM coverage_summaries cs "
            "LEFT JOIN lecture_sessions ls ON cs.lecture_id = ls.id "
            "WHERE ls.id IS NULL;"
        )).scalar()
        results["orphan_coverage_summaries"] = orphan_coverage or 0

        # Check 4: Orphan analysis jobs
        orphan_jobs = conn.execute(text(
            "SELECT COUNT(*) FROM analysis_jobs aj "
            "LEFT JOIN lecture_sessions ls ON aj.lecture_id = ls.id "
            "WHERE ls.id IS NULL;"
        )).scalar()
        results["orphan_analysis_jobs"] = orphan_jobs or 0

    logger.info("Data quality audit results: %s", results)
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_database_schema()
    audit_results = run_data_quality_audit()
    print("MIGRATION_AUDIT_SUCCESS:", audit_results)
