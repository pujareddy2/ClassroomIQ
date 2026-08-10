"""
================================================================================
database.py — SQLAlchemy Engine Configuration
================================================================================

WHY THIS FILE EXISTS:
    Every database operation in SQLAlchemy starts with an Engine. The Engine
    is the single point of contact between your Python code and PostgreSQL.
    This file reads the connection string, builds the Engine with production-
    safe pooling settings, and exports it so every other module uses the
    SAME engine — never creates a second one.

RESPONSIBILITY:
    1. Load DATABASE_URL from the .env file.
    2. Create one SQLAlchemy Engine for the entire process lifetime.
    3. Configure connection pooling so the app doesn't open a new TCP
       connection for every request (extremely expensive).
    4. Export `engine` for use by session.py and init_db.py.

HOW IT CONNECTS WITH THE REST OF THE BACKEND:
    database.py → session.py (uses the engine to build SessionLocal)
                → init_db.py (uses the engine to run CREATE TABLE)
                → main.py   (indirectly — called via init_db on startup)

FUTURE MODULES THAT DEPEND ON THIS FILE:
    Authentication, Curriculum Intelligence, RAG Pipeline, Coverage Analysis,
    Recommendations, Reports — every module that touches the database uses
    the SessionLocal which is built on top of this engine.

BEST PRACTICES USED:
    ✔ One engine per process (singleton pattern).
    ✔ Connection pooling configured explicitly (not left to defaults).
    ✔ pool_pre_ping to detect stale/dead connections.
    ✔ echo=False in production (never log raw SQL to stdout in production).
    ✔ Raises on startup if DATABASE_URL is missing (fail-fast).
================================================================================
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

# ── Environment Loading ────────────────────────────────────────────────────────
# Locate the project root (.env lives at ClassroomIQ/.env).
# This file is at: ClassroomIQ/backend/app/db/database.py
# Parents: db/ → app/ → backend/ → ClassroomIQ/
_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parents[3]  # 3 levels up from this file to ClassroomIQ/

_dotenv_path = _PROJECT_ROOT / ".env"
if not _dotenv_path.exists():
    # Fallback: look in the backend directory itself
    _dotenv_path = _HERE.parents[2] / ".env"

load_dotenv(dotenv_path=str(_dotenv_path))

# ── Database URL ───────────────────────────────────────────────────────────────
# Required format:
#   postgresql+psycopg2://username:password@host:port/database_name
#
# The "+psycopg2" part explicitly tells SQLAlchemy to use the psycopg2 driver.
# Without it, SQLAlchemy still picks psycopg2 by default, but being explicit
# avoids surprises when switching drivers (e.g., asyncpg for async support).
DATABASE_URL: str = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    raise ValueError(
        "\n\n[ClassroomIQ] DATABASE_URL is not set!\n"
        f"Expected a .env file at: {_dotenv_path}\n"
        "Example: DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/classroomiq_db\n"
    )

# Normalise legacy 'postgres://' URLs (Heroku style) to 'postgresql+psycopg2://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+psycopg2" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# ── SQLAlchemy Engine ──────────────────────────────────────────────────────────
#
# WHY ONLY ONE ENGINE?
#   An Engine manages a pool of real TCP connections to PostgreSQL. Creating
#   a second Engine creates a second pool, wasting connections, memory, and
#   causing subtle transaction isolation bugs. Import this `engine` object
#   everywhere — never call create_engine() twice.
#
# HOW ENGINE COMMUNICATES WITH POSTGRESQL:
#   Engine → Connection Pool → psycopg2 TCP socket → PostgreSQL process
#   When code needs a DB connection, the pool lends one from its internal
#   queue rather than opening a new TCP socket every time.
#
# HOW FUTURE API REQUESTS USE IT:
#   FastAPI request → session.py's get_db() → SessionLocal(bind=engine)
#   → SQLAlchemy ORM → engine.connect() → pool → psycopg2 → PostgreSQL

engine: Engine = create_engine(
    DATABASE_URL,
    # ── Connection Pool Settings ──────────────────────────────────────────
    #
    # pool_size: Number of connections kept open permanently.
    #   Too small  → requests queue and time out under load.
    #   Too large  → PostgreSQL max_connections limit is hit.
    #   Good default for a small-to-medium app: 10.
    pool_size=10,
    #
    # max_overflow: Extra connections allowed ABOVE pool_size when the pool
    #   is fully occupied. After pool_size + max_overflow connections are
    #   all in use, the next request raises TimeoutError.
    #   Setting this to 20 means up to 30 total connections are possible.
    max_overflow=20,
    #
    # pool_timeout: How many seconds a request will WAIT for a free
    #   connection before raising TimeoutError.
    #   30 seconds is the standard safe value.
    pool_timeout=30,
    #
    # pool_recycle: Connections older than this many seconds are replaced.
    #   Useful when infrastructure (LB, proxy, firewall, managed DB) drops
    #   long-lived idle TCP connections. Recycling helps avoid stale sockets.
    pool_recycle=1800,
    #
    # pool_pre_ping: Before lending a connection from the pool, SQLAlchemy
    #   sends a lightweight "SELECT 1" to PostgreSQL. If it fails (network
    #   glitch, DB restart), the dead connection is discarded and a fresh
    #   one is created. This is the single most important setting for
    #   production reliability.
    pool_pre_ping=True,
    #
    # ── Logging ──────────────────────────────────────────────────────────
    #
    # echo=False: Do NOT log every SQL statement to stdout.
    #   In development you can temporarily set this to True for debugging,
    #   but NEVER in production — it leaks sensitive data and drowns logs.
    echo=False,
    #
    # echo_pool=False: Do NOT log pool checkout/checkin events.
    echo_pool=False,
    # pool_use_lifo=True reuses recently used connections first, which often
    # works better with server-side idle timeout behaviour.
    pool_use_lifo=True,
)


# ── Optional: Log slow queries in production ───────────────────────────────────
# Uncomment this block if you want a warning for queries taking >1 second.
# This uses SQLAlchemy's event system — no external dependency required.
#
# @event.listens_for(engine, "before_cursor_execute")
# def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
#     import time
#     conn.info.setdefault("query_start_time", []).append(time.monotonic())
#
# @event.listens_for(engine, "after_cursor_execute")
# def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
#     import time, logging
#     elapsed = time.monotonic() - conn.info["query_start_time"].pop(-1)
#     if elapsed > 1.0:
#         logging.getLogger(__name__).warning(
#             "Slow query (%.2fs): %.200s", elapsed, statement
#         )
