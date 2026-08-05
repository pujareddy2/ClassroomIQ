import pytest
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.api.auth import get_current_user
from app.main import app

# Ensure database tables exist before running test suite
init_db()


@pytest.fixture(autouse=True)
def bypass_auth_for_domain_tests():
    """Domain tests exercise services; dedicated contract tests cover JWT rejection."""
    app.dependency_overrides[get_current_user] = lambda: None
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
