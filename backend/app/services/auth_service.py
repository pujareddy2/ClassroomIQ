from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.institution import Institution
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserPublic


def get_user_by_email(db: Session, email: str) -> User | None:
    normalized_email = email.strip().lower()
    stmt = select(User).where(User.email == normalized_email)
    return db.execute(stmt).scalar_one_or_none()


def get_or_create_default_institution(db: Session) -> Institution:
    default_name = "Default Institution"
    stmt = select(Institution).where(func.lower(Institution.name) == default_name.lower())
    institution = db.execute(stmt).scalar_one_or_none()
    if institution is not None:
        return institution

    institution = Institution(name=default_name, contact_email="default@institution.local")
    db.add(institution)
    db.flush()
    db.refresh(institution)
    return institution


def get_or_create_department(db: Session, institution_id: str, code: str, name: str) -> Department:
    normalized_code = code.strip().upper()
    normalized_name = name.strip()
    stmt = select(Department).where(
        Department.institution_id == institution_id,
        func.lower(Department.code) == normalized_code.lower(),
    )
    department = db.execute(stmt).scalar_one_or_none()
    if department is not None:
        return department

    department = Department(
        institution_id=institution_id,
        code=normalized_code,
        name=normalized_name,
    )
    db.add(department)
    db.flush()
    db.refresh(department)
    return department


def register_user(db: Session, payload: RegisterRequest) -> User:
    existing = get_user_by_email(db, payload.email)
    if existing:
        raise ValueError("Email is already registered")

    user = User(
        full_name=payload.full_name.strip(),
        email=payload.email.strip().lower(),
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )

    db.add(user)
    db.flush()

    if payload.role == "faculty":
        employee_id = payload.employee_id.strip() if payload.employee_id else f"FAC_{str(user.id)[:8].upper()}"

        institution = get_or_create_default_institution(db)
        department_code = payload.department_code or payload.department_name or "GENERAL"
        department_name = payload.department_name or "General"
        department = get_or_create_department(db, institution.id, department_code, department_name)

        faculty = Faculty(
            user_id=user.id,
            department_id=department.id,
            employee_id=employee_id,
            designation=payload.designation.strip() if payload.designation else None,
        )
        db.add(faculty)

    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, payload: LoginRequest) -> TokenResponse:
    user = get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise ValueError("Invalid email or password")

    if not user.is_active:
        raise ValueError("User account is inactive")

    token = create_access_token(
        subject=str(user.id),
        extra_claims={"email": user.email, "role": user.role},
    )

    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))
