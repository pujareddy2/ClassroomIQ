"""
================================================================================
base.py — SQLAlchemy Declarative Base & Model Registry
================================================================================

WHY THIS FILE EXISTS:
    SQLAlchemy needs a central "registry" that knows about ALL ORM models
    before it can generate or verify the database schema. That registry is
    called the Declarative Base (Base). This file:
      1. Defines `Base` — the class every ORM model must inherit from.
      2. Imports every model module so Python registers them with Base.
      3. Exports `Base` so Alembic can read Base.metadata and generate
         migration scripts automatically.

    Without this file, Alembic's `--autogenerate` would produce empty
    migration files because it wouldn't know any models exist.

RESPONSIBILITY:
    - Own the single, shared `Base` instance.
    - Act as the model registry (all models must be imported here).
    - Be the ONE place Alembic looks at to understand the full schema.

HOW IT CONNECTS WITH THE REST OF THE BACKEND:
    base.py ← base_class.py (defines the Base class)
    base.py → every model file (imports them to register with metadata)
    base.py → init_db.py (uses Base.metadata.create_all)
    base.py → alembic/env.py (target_metadata = Base.metadata)

WHY EVERY ORM MODEL INHERITS FROM BASE:
    When a class inherits from Base, SQLAlchemy reads its `__tablename__`
    and column definitions, then adds a Table object to Base.metadata.
    Base.metadata is a dictionary-like object that maps table names to
    Table definitions. Alembic reads this metadata to figure out what the
    schema SHOULD look like, then compares it to what currently EXISTS in
    PostgreSQL to generate migration diffs.

HOW ALEMBIC DEPENDS ON BASE:
    In alembic/env.py you will set:
        from app.db.base import Base
        target_metadata = Base.metadata
    Alembic then calls:
        Base.metadata.create_all(engine)   ← for fresh tables
        Base.metadata.compare_to(...)      ← for migration diffs

BEST PRACTICES USED:
        ✔ All model imports in one place → no scattered imports across the project.
        ✔ Single side-effect import (`import app.models`) keeps import blocks tidy.
        ✔ Base metadata stays Alembic-ready for `--autogenerate` workflows.
================================================================================
"""

import importlib

from app.db.base_class import Base

# ── Model Imports ──────────────────────────────────────────────────────────────
#
# WHY IMPORT ALL MODELS HERE?
#   Python only executes a module's code when it is first imported.
#   SQLAlchemy only knows about a model's table when the model CLASS is
#   defined (i.e., when Python runs the class body). If a model file is
#   never imported, its table never appears in Base.metadata.
#
# `app.models` imports every model class in `app/models/__init__.py`,
# which ensures each table class is registered into Base.metadata.
importlib.import_module("app.models")

__all__ = ["Base"]

# ── Verify registration (optional, useful for debugging) ───────────────────────
# Uncomment during development to list all registered table names:
# print("Registered tables:", list(Base.metadata.tables.keys()))
