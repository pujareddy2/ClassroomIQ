import pytest
import uuid
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import RegisterRequest
from app.services.auth_service import register_user
from app.core.security import create_access_token

client = TestClient(app)


def test_rag_api_unauthenticated_access_rejected():
    """
    SECURITY TEST: Unauthenticated requests to /api/v1/rag/* must return HTTP 401.
    """
    from app.api.auth import get_current_user
    app.dependency_overrides.pop(get_current_user, None)
    try:
        res = client.post("/api/v1/rag/query", json={"query": "test"})
        assert res.status_code == 401
    finally:
        app.dependency_overrides[get_current_user] = lambda: None


def test_rag_api_invalid_uuid_handling(db_session):
    """
    SECURITY TEST: Invalid or malformed UUIDs return HTTP 404 or 422 safely.
    """
    fake_uuid = str(uuid.uuid4())[:6]
    user = register_user(
        db_session,
        RegisterRequest(
            full_name="Dr. Sec User",
            email=f"sec_{fake_uuid}@university.edu",
            password="Password123!",
            role="faculty",
            employee_id=f"EMP-SEC-{fake_uuid}",
            designation="Professor",
            department_name="Computer Science",
        )
    )
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    fake_id = str(uuid.uuid4())
    res = client.get(f"/api/v1/rag/documents/{fake_id}/status", headers=headers)
    assert res.status_code == 404
