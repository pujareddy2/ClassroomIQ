"""
ClassroomIQ — Comprehensive API Contract, Forensic & Database Consistency Test Suite.
"""

import uuid
from typing import Dict, Any
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.api.auth import get_current_user
from app.models.curriculum import Curriculum
from app.models.faculty import Faculty
from app.models.lecture_session import LectureSession

# Mock authenticated user identity
class MockUser:
    id = uuid.uuid4()
    email = "test.faculty@classroomiq.edu"
    full_name = "Dr. Test Faculty"
    role = "faculty"

app.dependency_overrides[get_current_user] = lambda: MockUser()

client = TestClient(app)

@pytest.fixture
def test_data(db_session: Session) -> Dict[str, Any]:
    active_curriculum = db_session.query(Curriculum).first()
    curriculum_id = str(active_curriculum.id) if active_curriculum else str(uuid.uuid4())
    course_id = str(active_curriculum.course_id) if active_curriculum else str(uuid.uuid4())
    
    active_faculty = db_session.query(Faculty).first()
    faculty_id = str(active_faculty.id) if active_faculty else str(uuid.uuid4())
    
    active_lecture = db_session.query(LectureSession).first()
    lecture_id = str(active_lecture.id) if active_lecture else None

    return {
        "curriculum_id": curriculum_id,
        "course_id": course_id,
        "faculty_id": faculty_id,
        "lecture_id": lecture_id,
    }

def test_health_check_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "healthy"

def test_validation_engine_complete_pipeline(test_data: Dict[str, Any]):
    payload = {
        "course_id": test_data["course_id"],
        "transcript_chunks": [
            {
                "chunk_id": "c1",
                "speaker": "Faculty",
                "start_time": 0.0,
                "end_time": 40.0,
                "text": "A compiler is a program that translates source code into machine code."
            }
        ]
    }
    r = client.post("/api/v1/validation/analyze", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    lecture_id = data["lecture_id"]
    test_data["lecture_id"] = lecture_id
    assert "validated_chunks" in data
    assert "overall_validation_score" in data

    # Test GET endpoints
    r2 = client.get(f"/api/v1/validation/{lecture_id}")
    assert r2.status_code == 200
    assert isinstance(r2.json()["data"], list)

    r3 = client.get(f"/api/v1/validation/{lecture_id}/summary")
    assert r3.status_code == 200
    assert "overall_validation_score" in r3.json()["data"]

    r4 = client.get(f"/api/v1/validation/{lecture_id}/evidence")
    assert r4.status_code == 200
    assert isinstance(r4.json()["data"], list)

    r5 = client.get(f"/api/v1/validation/{lecture_id}/timeline")
    assert r5.status_code == 200
    assert "intervals" in r5.json()["data"]

def test_coverage_engine_pipeline(test_data: Dict[str, Any]):
    lecture_id = test_data["lecture_id"] or str(uuid.uuid4())
    payload = {
        "lecture_id": lecture_id,
        "course_id": test_data["course_id"],
        "curriculum_id": test_data["curriculum_id"],
        "chunks": [
            {
                "chunk_id": "c1",
                "speaker": "Faculty",
                "start_time": 0.0,
                "end_time": 40.0,
                "text": "A compiler translates source code."
            }
        ]
    }
    r = client.post("/api/v1/coverage/analyze", json=payload)
    assert r.status_code == 201, r.text

    r_sum = client.get(f"/api/v1/coverage/{lecture_id}")
    assert r_sum.status_code == 200

    r_top = client.get(f"/api/v1/coverage/{lecture_id}/topics")
    assert r_top.status_code == 200

    r_rem = client.get(f"/api/v1/coverage/{lecture_id}/remaining")
    assert r_rem.status_code == 200

    r_time = client.get(f"/api/v1/coverage/{lecture_id}/timeline")
    assert r_time.status_code == 200

def test_teaching_intelligence_pipeline(test_data: Dict[str, Any]):
    lecture_id = test_data["lecture_id"] or str(uuid.uuid4())
    payload = {
        "lecture_id": lecture_id,
        "curriculum_id": test_data["curriculum_id"],
        "faculty_id": test_data["faculty_id"],
        "transcript_chunks": [
            {
                "chunk_id": "c1",
                "speaker": "Faculty",
                "start_time": 0.0,
                "end_time": 40.0,
                "text": "For example, in compiler design we use lexical analysis."
            }
        ]
    }
    r = client.post("/api/v1/teaching/analyze", json=payload)
    assert r.status_code == 201, r.text

    r_get = client.get(f"/api/v1/teaching/{lecture_id}")
    assert r_get.status_code == 200

    r_sum = client.get(f"/api/v1/teaching/{lecture_id}/summary")
    assert r_sum.status_code == 200

    r_str = client.get(f"/api/v1/teaching/{lecture_id}/strengths")
    assert r_str.status_code == 200

    r_weak = client.get(f"/api/v1/teaching/{lecture_id}/weaknesses")
    assert r_weak.status_code == 200

    r_ex = client.get(f"/api/v1/teaching/{lecture_id}/examples")
    assert r_ex.status_code == 200

    r_int = client.get(f"/api/v1/teaching/{lecture_id}/interaction")
    assert r_int.status_code == 200

    r_struct = client.get(f"/api/v1/teaching/{lecture_id}/structure")
    assert r_struct.status_code == 200

def test_recommendation_engine_pipeline(test_data: Dict[str, Any]):
    lecture_id = test_data["lecture_id"] or str(uuid.uuid4())
    r = client.post("/api/v1/recommendations/generate", json={"lecture_id": lecture_id})
    assert r.status_code == 201, r.text

    r_get = client.get(f"/api/v1/recommendations/{lecture_id}")
    assert r_get.status_code == 200

    r_prio = client.get(f"/api/v1/recommendations/{lecture_id}/priority")
    assert r_prio.status_code == 200

    r_ev = client.get(f"/api/v1/recommendations/{lecture_id}/evidence")
    assert r_ev.status_code == 200

    r_w = client.get(f"/api/v1/recommendations/faculty/{test_data['faculty_id']}/weekly")
    assert r_w.status_code == 200

    r_m = client.get(f"/api/v1/recommendations/faculty/{test_data['faculty_id']}/monthly")
    assert r_m.status_code == 200

    r_h = client.get(f"/api/v1/recommendations/faculty/{test_data['faculty_id']}/history")
    assert r_h.status_code == 200

def test_explanation_xai_pipeline(test_data: Dict[str, Any]):
    lecture_id = test_data["lecture_id"] or str(uuid.uuid4())
    r = client.post("/api/v1/explanations/generate", json={"lecture_id": lecture_id})
    assert r.status_code in [201, 409], r.text

    r_get = client.get(f"/api/v1/explanations/{lecture_id}")
    assert r_get.status_code == 200

    r_sum = client.get(f"/api/v1/explanations/{lecture_id}/summary")
    assert r_sum.status_code == 200

    r_ev = client.get(f"/api/v1/explanations/{lecture_id}/evidence")
    assert r_ev.status_code == 200

    r_tr = client.get(f"/api/v1/explanations/{lecture_id}/transcripts")
    assert r_tr.status_code == 200

    r_cit = client.get(f"/api/v1/explanations/{lecture_id}/citations")
    assert r_cit.status_code == 200

    r_conf = client.get(f"/api/v1/explanations/{lecture_id}/confidence")
    assert r_conf.status_code == 200

    r_reas = client.get(f"/api/v1/explanations/{lecture_id}/reasoning")
    assert r_reas.status_code == 200

    r_time = client.get(f"/api/v1/explanations/{lecture_id}/timeline")
    assert r_time.status_code == 200

def test_rag_and_assistant_pipeline(test_data: Dict[str, Any]):
    r_rag = client.post("/api/v1/rag/query", json={"query": "What is a compiler?", "course_id": test_data["course_id"], "top_k": 3})
    assert r_rag.status_code == 200, r_rag.text

    r_ask = client.post("/api/v1/assistant/ask", json={"question": "What is a compiler?", "course_id": test_data["course_id"]})
    assert r_ask.status_code == 200, r_ask.text

    r_chat = client.post("/api/v1/assistant/chat", json={"question": "Explain compiler optimization", "course_id": test_data["course_id"]})
    assert r_chat.status_code == 200, r_chat.text

def test_curriculum_endpoints(test_data: Dict[str, Any]):
    curriculum_id = test_data["curriculum_id"]
    
    r_tree = client.get(f"/api/v1/curriculum/{curriculum_id}/tree")
    assert r_tree.status_code == 200

    r_stats = client.get(f"/api/v1/curriculum/{curriculum_id}/statistics")
    assert r_stats.status_code == 200

    r_seg = client.get(f"/api/v1/curriculum/{curriculum_id}/segments")
    assert r_seg.status_code == 200

def test_workflow_and_analysis_status_endpoints(test_data: Dict[str, Any]):
    lecture_id = test_data["lecture_id"] or str(uuid.uuid4())
    
    r_wf = client.get(f"/api/v1/workflow/{lecture_id}/status")
    assert r_wf.status_code == 200

    r_an = client.get(f"/api/v1/analysis/status/{lecture_id}")
    assert r_an.status_code == 200

def test_negative_input_contracts():
    # Test missing required field
    r_bad_post = client.post("/api/v1/validation/analyze", json={})
    assert r_bad_post.status_code == 422

    # Test non-existent UUID resource
    fake_id = str(uuid.uuid4())
    r_not_found = client.get(f"/api/v1/validation/{fake_id}")
    assert r_not_found.status_code == 404
