"""
================================================================================
session.py — SQLAlchemy Session Factory & FastAPI Dependency
================================================================================

WHY THIS FILE EXISTS:
    An Engine manages the connection pool. A Session manages a single
    *unit of work* — a conversation between your code and the database.
    Every HTTP request must get its own isolated Session so that:
      - Transactions don't bleed across requests.
      - One failed request doesn't corrupt another's data.
      - Sessions are always closed (connections returned to the pool).

RESPONSIBILITY:
    1. Create `SessionLocal` — a factory that produces Session objects
       bound to our engine.
    2. Expose `get_db()` — a FastAPI dependency that opens a Session at
       the start of a request, yields it to the route handler, then
       guarantees it is closed in the finally block — even if an exception
       is raised.

SESSION LIFECYCLE PER REQUEST:
    ┌──────────────────────────────────────────────────────────┐
    │  FastAPI receives HTTP request                           │
    │         ↓                                               │
    │  FastAPI calls get_db() (dependency injection)          │
    │         ↓                                               │
    │  db = SessionLocal()  ← new Session created              │
    │         ↓                                               │
    │  Route handler receives `db` via Depends(get_db)        │
    │         ↓                                               │
    │  Route calls db.query(...) / db.add(...) / db.commit()  │
    │         ↓                                               │
    │  On success  → db.commit()  (persists changes)          │
    │  On failure  → db.rollback() (reverts changes)          │
    │         ↓                                               │
    │  finally: db.close()  ← connection returned to pool     │
    └──────────────────────────────────────────────────────────┘

HOW IT CONNECTS WITH THE REST OF THE BACKEND:
    session.py ← database.py (imports engine)
    session.py → every API router (via Depends(get_db))
    session.py → every service / repository layer

FUTURE MODULES THAT DEPEND ON THIS FILE:
    All route handlers in:
      - api/v1/auth.py         (user login, registration)
      - api/v1/curriculum.py   (syllabus upload/parsing)
      - api/v1/coverage.py     (coverage analysis)
      - api/v1/validation.py   (technical validation flags)
      - api/v1/reports.py      (PDF report generation)
      - api/v1/recommendations.py

BEST PRACTICES USED:
    ✔ autocommit=False — never silently commit; code must call db.commit().
    ✔ autoflush=False  — don't auto-send pending changes to DB mid-transaction.
    ✔ Generator function with try/finally — guarantees session closure.
    ✔ Type annotation Generator[Session, None, None] for IDE support.
================================================================================
"""

from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from app.db.database import engine

# ── Session Factory ────────────────────────────────────────────────────────────
#
# `sessionmaker` returns a *class* (SessionLocal) — not a session instance.
# Every time you call SessionLocal() you get a fresh Session object.
#
# autocommit=False (CRITICAL):
#   SQLAlchemy will NOT automatically commit after every statement.
#   Your route handler is responsible for calling db.commit() when it
#   wants changes persisted. This enables proper transactional control:
#   you can do multiple inserts/updates and commit them all at once.
#   A beginner mistake is setting autocommit=True — this makes rollback
#   impossible and causes partial-write bugs.
#
# autoflush=False:
#   By default (autoflush=True), SQLAlchemy flushes (sends pending SQL to
#   the DB) before every query. This is often surprising:
#     db.add(new_user)          # not yet sent
#     db.query(User).all()      # triggers auto-flush → new_user now sent
#   Setting autoflush=False gives you explicit control. You decide when to
#   flush, which avoids accidentally sending half-built objects to the DB.
#
# bind=engine:
#   Tells the factory which Engine (and thus which connection pool) all
#   Sessions should use. This is how the session layer connects to the
#   database layer.

SessionLocal: sessionmaker[Session] = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ── FastAPI Dependency ─────────────────────────────────────────────────────────
#
# WHY A GENERATOR FUNCTION?
#   FastAPI's dependency injection system supports Python generators. When a
#   dependency is a generator (uses `yield`), FastAPI automatically:
#     1. Runs all code before `yield` → setup (open session).
#     2. Injects the yielded value into the route handler.
#     3. Runs all code after `yield` → teardown (close session).
#   The finally: block runs even if the route raises an exception.
#
# COMMON BEGINNER MISTAKES:
#   ✗ NOT closing the session → connections leak, pool exhausts → 503 errors.
#   ✗ Opening a session per query instead of per request → no transaction scope.
#   ✗ Sharing one global session across requests → race conditions.
#
# HOW TO USE IN A ROUTE:
#   from fastapi import Depends
#   from sqlalchemy.orm import Session
#   from app.db.session import get_db
#
#   @router.get("/users")
#   def list_users(db: Session = Depends(get_db)):
#       return db.query(User).all()

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session per request.

    Usage:
        @router.get("/example")
        def example_route(db: Session = Depends(get_db)):
            ...
    """
    db: Session = SessionLocal()
    try:
        yield db
        # If the route handler calls db.commit() explicitly, this is a no-op.
        # If you want ALL successful requests to auto-commit, you can add
        # db.commit() here — but explicit commits in the service layer are cleaner.
    except Exception:
        # If anything goes wrong inside the route, roll back the entire
        # transaction so no partial data is written to the DB.
        db.rollback()
        raise
    finally:
        # ALWAYS close the session. This returns the underlying connection
        # back to the pool so the next request can use it.
        db.close()
