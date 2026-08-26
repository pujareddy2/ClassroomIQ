import pytest
import uuid
import io
import asyncio
from fastapi import UploadFile
from fastapi.testclient import TestClient

from app.schemas.auth import RegisterRequest
from app.services.auth_service import register_user
from app.services.reference_service import ReferenceService
from app.schemas.reference_material import ReferenceUploadMetadata
from app.main import app
from app.core.security import create_access_token


def test_rag_api_full_suite(db_session):
    r_id = str(uuid.uuid4())[:8]
    email = f"rag_api_suite_{r_id}@university.edu"
    reg = RegisterRequest(
        full_name=f"Dr. API Suite Faculty {r_id}",
        email=email,
        password="Password123!",
        role="faculty",
        employee_id=f"EMP-APISUITE-{r_id}",
        designation="Professor",
        department_name="Computer Science",
    )
    user = register_user(db_session, reg)

    ref_service = ReferenceService(db_session)
    meta = ReferenceUploadMetadata(
        course_name=f"CS601 Distributed Systems {r_id}",
        academic_year="2026-2027",
        semester="1",
        faculty_name=user.full_name,
        title=f"Distributed Systems {r_id}",
        document_type="REFERENCE_BOOK",
    )

    doc_text = """
CHAPTER 1: CONSENSUS ALGORITHMS
Paxos and Raft are consensus algorithms for maintaining state machine replication across a distributed network.
    """
    fake_file = UploadFile(filename="distributed.txt", file=io.BytesIO(doc_text.encode("utf-8")), headers={"content-type": "text/plain"})
    created_ref, _ = asyncio.run(ref_service.upload_reference_material(meta, fake_file))

    client = TestClient(app)
    token = create_access_token(subject=str(user.id), extra_claims={"email": user.email, "role": user.role})
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Index Endpoint
    idx_res = client.post(f"/api/v1/rag/index/{created_ref.id}", headers=headers)
    assert idx_res.status_code == 200
    assert idx_res.json()["data"]["status"] == "SUCCESS"
    assert "chunks_created" in idx_res.json()["data"]

    # 2. Query Endpoint
    q_payload = {"query": "Raft consensus state machine", "course_id": str(created_ref.course_id)}
    q_res = client.post("/api/v1/rag/query", headers=headers, json=q_payload)
    assert q_res.status_code == 200
    assert q_res.json()["data"]["status"] == "SUCCESS"
    assert len(q_res.json()["data"]["evidence"]) > 0

    # 3. Chunks List Endpoint
    c_res = client.get(f"/api/v1/rag/documents/{created_ref.id}/chunks", headers=headers)
    assert c_res.status_code == 200
    assert c_res.json()["data"]["status"] == "SUCCESS"
    assert len(c_res.json()["data"]["chunks"]) > 0

    # 4. Status Endpoint
    s_res = client.get(f"/api/v1/rag/documents/{created_ref.id}/status", headers=headers)
    assert s_res.status_code == 200
    assert s_res.json()["data"]["status"] == "SUCCESS"
    assert s_res.json()["data"]["processing_status"] == "EMBEDDED"

    # 5. Reindex Endpoint
    re_res = client.post(f"/api/v1/rag/reindex/{created_ref.id}", headers=headers)
    assert re_res.status_code == 200
    assert re_res.json()["data"]["status"] == "SUCCESS"
