"""
Integration tests for Curriculum Hierarchy REST APIs.
"""

import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.database import engine
from app.main import app
from app.models.academic_term import AcademicTerm
from app.models.course import Course
from app.models.curriculum import Curriculum
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.institution import Institution
from app.models.topic import Topic
from app.models.user import User

client = TestClient(app)


def test_curriculum_hierarchy_apis():
    with Session(engine) as db:
        # Create test records
        inst = db.query(Institution).first()
        if not inst:
            inst = Institution(name="Test Univ API", contact_email="api@test.edu")
            db.add(inst)
            db.flush()

        dept = db.query(Department).filter_by(institution_id=inst.id).first()
        if not dept:
            dept = Department(institution_id=inst.id, name="Computer Science API", code="CS_API")
            db.add(dept)
            db.flush()

        user = db.query(User).filter_by(email="api.faculty@test.edu").first()
        if not user:
            user = User(full_name="Dr. API Faculty", email="api.faculty@test.edu", password_hash="pw", role="FACULTY")
            db.add(user)
            db.flush()

        faculty = db.query(Faculty).filter_by(user_id=user.id).first()
        if not faculty:
            faculty = Faculty(user_id=user.id, department_id=dept.id, employee_id=f"EMP_API_{uuid.uuid4().hex[:4]}")
            db.add(faculty)
            db.flush()

        course = db.query(Course).filter_by(course_code="CS_API_101").first()
        if not course:
            course = Course(department_id=dept.id, course_code="CS_API_101", course_name="API Testing Course", credits=3)
            db.add(course)
            db.flush()

        term = db.query(AcademicTerm).filter_by(institution_id=inst.id, academic_year="2025-2026", semester="1").first()
        if not term:
            import datetime
            term = AcademicTerm(institution_id=inst.id, academic_year="2025-2026", semester="1", start_date=datetime.date(2025, 8, 1), end_date=datetime.date(2025, 12, 31))
            db.add(term)
            db.flush()

        curriculum = Curriculum(
            course_id=course.id,
            academic_term_id=term.id,
            faculty_id=faculty.id,
            title="API Test Curriculum Hierarchy",
            document_type="SYLLABUS",
            file_name="api_test.pdf",
            file_path="/tmp/api_test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            syllabus_version=f"v_api_{uuid.uuid4().hex[:4]}",
            processing_status="PARSED",
            extracted_text="Unit 1: API Basics\nTopics\nEndpoints",
        )
        db.add(curriculum)
        db.flush()

        # Add topic rows
        unit_id = uuid.uuid4()
        chap_id = uuid.uuid4()
        top_id = uuid.uuid4()

        db.add(Topic(id=unit_id, curriculum_id=curriculum.id, parent_topic_id=None, topic_name="Unit 1: API Basics", node_type="UNIT", display_order=1, sequence_number=1))
        db.add(Topic(id=chap_id, curriculum_id=curriculum.id, parent_topic_id=unit_id, topic_name="Topics", node_type="CHAPTER", display_order=1, sequence_number=1))
        db.add(Topic(id=top_id, curriculum_id=curriculum.id, parent_topic_id=chap_id, topic_name="Endpoints", node_type="TOPIC", display_order=1, sequence_number=1))
        db.commit()

        curr_id_str = str(curriculum.id)
        top_id_str = str(top_id)

    # 1. Test GET /api/v1/curriculum/{curriculum_id}
    res = client.get(f"/api/v1/curriculum/{curr_id_str}")
    assert res.status_code == 200
    data = res.json()["data"] if "data" in res.json() else res.json()
    assert "curriculum" in data
    assert data["curriculum"]["title"] == "API Test Curriculum Hierarchy"
    assert len(data["curriculum"]["units"]) == 1

    # 2. Test GET /api/v1/curriculum/{curriculum_id}/tree
    res_tree = client.get(f"/api/v1/curriculum/{curr_id_str}/tree")
    assert res_tree.status_code == 200
    tree_data = res_tree.json()["data"] if "data" in res_tree.json() else res_tree.json()
    assert len(tree_data["tree"]) == 1

    # 3. Test GET /api/v1/curriculum/{curriculum_id}/segments
    res_seg = client.get(f"/api/v1/curriculum/{curr_id_str}/segments")
    assert res_seg.status_code == 200
    seg_data = res_seg.json()["data"] if "data" in res_seg.json() else res_seg.json()
    assert seg_data["total_segments"] == 1
    assert seg_data["segments"][0]["hierarchy_path"] == ["Unit 1: API Basics", "Topics"]

    # 4. Test GET /api/v1/curriculum/{curriculum_id}/statistics
    res_stat = client.get(f"/api/v1/curriculum/{curr_id_str}/statistics")
    assert res_stat.status_code == 200
    stat_data = res_stat.json()["data"] if "data" in res_stat.json() else res_stat.json()
    assert stat_data["statistics"]["units"] == 1

    # 5. Test GET /api/v1/curriculum/{curriculum_id}/node/{node_id} (Task 7)
    res_node = client.get(f"/api/v1/curriculum/{curr_id_str}/node/{top_id_str}")
    assert res_node.status_code == 200
    node_data = res_node.json()["data"] if "data" in res_node.json() else res_node.json()
    assert node_data["node"]["title"] == "Endpoints"
    assert node_data["node"]["hierarchy_path"] == ["Unit 1: API Basics", "Topics", "Endpoints"]

    # 6. Test 404 for invalid curriculum_id
    res_404 = client.get(f"/api/v1/curriculum/{uuid.uuid4()}")
    assert res_404.status_code == 404
