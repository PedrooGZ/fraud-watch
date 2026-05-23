from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import User


def get_user_by_email(db: Session, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    return db.scalar(stmt)


def get_user_by_id(db: Session, user_id: int) -> User | None:
    stmt = select(User).where(User.id == user_id)
    return db.scalar(stmt)


def create_user(
    db: Session,
    *,
    email: str,
    full_name: str,
    role: str,
    password_hash: str,
    is_active: bool = True,
) -> User:
    user = User(
        email=email,
        full_name=full_name,
        role=role,
        password_hash=password_hash,
        is_active=is_active,
    )
    db.add(user)
    return user
