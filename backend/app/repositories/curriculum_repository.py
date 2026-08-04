from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.academic_term import AcademicTerm
from app.models.course import Course
from app.models.curriculum import Curriculum
from app.models.faculty import Faculty
from app.models.user import User


class CurriculumRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_course(self, course_id: UUID) -> Course | None:
        return self.db.get(Course, course_id)

    def get_course_by_selector(self, selector: str) -> Course | None:
        normalized_selector = selector.strip().lower()
        stmt = select(Course).where(
            func.lower(Course.course_code) == normalized_selector,
        )
        course = self.db.execute(stmt).scalar_one_or_none()
        if course is not None:
            return course

        stmt = select(Course).where(
            func.lower(Course.course_name) == normalized_selector,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_faculty(self, faculty_id: UUID) -> Faculty | None:
        return self.db.get(Faculty, faculty_id)

    def get_faculty_by_user_id(self, faculty_user_id: UUID) -> Faculty | None:
        stmt = select(Faculty).where(Faculty.user_id == faculty_user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_faculty_by_name(self, faculty_name: str) -> Faculty | None:
        normalized_name = faculty_name.strip().lower()
        # join using the ORM relationship to disambiguate multiple foreign keys
        stmt = select(Faculty).join(Faculty.user).where(func.lower(User.full_name) == normalized_name)
        faculty_matches = self.db.execute(stmt).scalars().all()
        if not faculty_matches:
            return None
        if len(faculty_matches) > 1:
            raise LookupError(f"Faculty name '{faculty_name}' is ambiguous")
        return faculty_matches[0]

    def get_academic_term(self, academic_term_id: UUID) -> AcademicTerm | None:
        return self.db.get(AcademicTerm, academic_term_id)

    def get_academic_term_by_details(self, institution_id: UUID, academic_year: str, semester: int) -> AcademicTerm | None:
        stmt = select(AcademicTerm).where(
            AcademicTerm.institution_id == institution_id,
            func.lower(AcademicTerm.academic_year) == academic_year.strip().lower(),
            AcademicTerm.semester == str(semester),
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_or_create_academic_term(
        self,
        institution_id: UUID,
        academic_year: str,
        semester: int,
        start_date: date,
        end_date: date,
    ) -> AcademicTerm:
        academic_term = self.get_academic_term_by_details(institution_id, academic_year, semester)
        if academic_term is not None:
            return academic_term

        academic_term = AcademicTerm(
            institution_id=institution_id,
            academic_year=academic_year.strip(),
            semester=str(semester),
            start_date=start_date,
            end_date=end_date,
        )
        self.db.add(academic_term)
        self.db.flush()
        self.db.refresh(academic_term)
        return academic_term

    def count_curricula_for_course_term(self, course_id: UUID, academic_term_id: UUID) -> int:
        stmt = select(func.count(Curriculum.id)).where(
            Curriculum.course_id == course_id,
            Curriculum.academic_term_id == academic_term_id,
        )
        return int(self.db.execute(stmt).scalar_one())

    def create_curriculum(self, curriculum: Curriculum) -> Curriculum:
        self.db.add(curriculum)
        self.db.flush()
        self.db.refresh(curriculum)
        return curriculum

    def create_course(self, course_code: str, course_name: str, department_id, credits: int = 3) -> Course:
        # If a course with the same code already exists, return it instead of raising
        normalized = course_code.strip().lower()
        stmt = select(Course).where(func.lower(Course.course_code) == normalized)
        existing = self.db.execute(stmt).scalar_one_or_none()
        if existing is not None:
            return existing

        course = Course(
            department_id=department_id,
            course_code=course_code,
            course_name=course_name,
            credits=credits,
        )
        self.db.add(course)
        self.db.flush()
        self.db.refresh(course)
        return course
