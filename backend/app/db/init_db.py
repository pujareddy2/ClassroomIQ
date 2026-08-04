"""
================================================================================
init_db.py — Database Table Initialization
================================================================================

WHY THIS FILE EXISTS (and why it is SEPARATE from database.py):
    database.py has one job: create the Engine.
    init_db.py has a different job: use the Engine to create tables.

    Keeping them separate follows the Single Responsibility Principle:
      - If you change connection pooling settings, you only touch database.py.
      - If you add a new table, you only touch this file.
      - Tests can import database.py without accidentally triggering table
        creation (a common source of test pollution).

    In production, table creation is handled by Alembic migrations.
    This file is used for:
      - Local development first-run setup.
      - Test environment setup (create tables in a test DB).
      - Seed data injection (future).
      - Docker entrypoint scripts.

RESPONSIBILITY:
    1. Import Base (and thus all models via base.py's side-effect imports).
    2. Call Base.metadata.create_all(engine) to create any missing tables.
       (This is idempotent — it does NOT drop or alter existing tables.)
    3. Provide a place to add seed/fixture data for development.
    4. Be callable from main.py startup event and from CLI scripts.

HOW IT CONNECTS WITH THE REST OF THE BACKEND:
    init_db.py ← database.py (imports engine)
    init_db.py ← base.py     (imports Base with all model metadata)
    init_db.py → main.py     (called in @app.on_event("startup") or lifespan)

    NOTE: In production, do NOT call init_db() in the startup event.
    Use Alembic migrations instead. Only call init_db() in development
    or test environments.

FUTURE MODULES THAT DEPEND ON THIS FILE:
    - Seed scripts for inserting default roles, admin users, sample courses.
    - Docker entrypoint (docker-entrypoint.sh calls `python -m app.db.init_db`).
    - pytest fixtures (call init_db with a test engine before test sessions).

BEST PRACTICES USED:
    ✔ checkfirst=True (implicit in create_all) → never drops existing tables.
    ✔ Logging instead of print() → respects the application log level.
    ✔ Separate create_tables() and seed_data() functions → testable units.
    ✔ if __name__ == "__main__": block → runnable as a standalone script.
================================================================================
"""

import logging

from sqlalchemy.engine import Engine

from app.db.base import Base
from app.db.database import engine

logger = logging.getLogger(__name__)


def create_tables(bind: Engine = engine) -> None:
    """
    Create all database tables defined in the ORM models.

    Uses Base.metadata.create_all() which:
      - Iterates over every Table registered in Base.metadata.
      - Issues a CREATE TABLE IF NOT EXISTS for each one.
      - Respects foreign key ordering (creates parent tables first).
      - Is SAFE to call multiple times — existing tables are not touched.

    Args:
        bind: The SQLAlchemy Engine to connect to.
              Defaults to the application engine from database.py.
              Tests can pass a test-DB engine here.

    Common Beginner Mistake:
        Calling Base.metadata.create_all(engine) without first importing
        all model files → tables are missing from metadata → they are
        not created. Always import via `from app.db.base import Base`
        which triggers all model imports as a side effect.
    """
    logger.info("Creating database tables (if they do not already exist)…")
    try:
        Base.metadata.create_all(bind=bind)
        table_names = list(Base.metadata.tables.keys())
        logger.info(
            "Database ready. %d table(s) registered: %s",
            len(table_names),
            ", ".join(sorted(table_names)),
        )
    except Exception as exc:
        logger.error("Failed to create database tables: %s", exc)
        raise


def seed_data(bind: Engine = engine) -> None:
    """
    Insert default / seed data required for the application to function.

    This function is intentionally left as a stub. Add seed logic here
    as the project grows. Examples:
      - Create a default 'superadmin' institution.
      - Insert default user roles.
      - Populate reference data tables.

    Args:
        bind: The SQLAlchemy Engine to connect to.
    """
    # TODO: Add seed data as the project grows.
    # Example pattern:
    #
    # from sqlalchemy.orm import Session
    # from app.models.institution import Institution
    #
    # with Session(bind) as db:
    #     if not db.query(Institution).first():
    #         db.add(Institution(name="Demo University", contact_email="admin@demo.edu"))
    #         db.commit()
    #         logger.info("Seeded default institution.")
    logger.info("seed_data() called — no seed data defined yet.")


def init_db(bind: Engine = engine) -> None:
    """
    Full database initialisation: create tables, then seed data.

    Call this from:
      - main.py startup event (development only).
      - Docker entrypoint scripts.
      - pytest session fixtures.

    In PRODUCTION, prefer Alembic migrations over create_tables().
    """
    create_tables(bind=bind)
    seed_data(bind=bind)


# ── CLI entry-point ────────────────────────────────────────────────────────────
# Run directly with:
#   python -m app.db.init_db
# or:
#   python app/db/init_db.py
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running database initialisation from CLI…")
    init_db()
    logger.info("Database initialisation complete.")
