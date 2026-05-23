from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.core.config import JWT_ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, JWT_SECRET_KEY
from src.repositories.user_repository import create_user, get_user_by_email, get_user_by_id
from src.schemas.auth_schema import RegisterRequest

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(*, subject: str | int, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except ExpiredSignatureError as exc:
        raise ValueError("Token expired.") from exc
    except InvalidTokenError as exc:
        raise ValueError("Invalid token.") from exc


def register_user(db: Session, request: RegisterRequest):
    email = str(request.email).strip().lower()
    if get_user_by_email(db, email) is not None:
        raise ValueError("Email already registered.")

    user = create_user(
        db,
        email=email,
        full_name=request.full_name.strip(),
        role=request.role,
        password_hash=hash_password(request.password),
        is_active=True,
    )
    return user


def authenticate_user(db: Session, email: str, password: str):
    normalized_email = email.strip().lower()
    user = get_user_by_email(db, normalized_email)
    if user is None or not bool(user.is_active):
        return None
    if not user.password_hash:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def get_current_user_from_token(db: Session, token: str):
    payload = decode_access_token(token)
    subject = payload.get("sub")
    if subject is None:
        raise ValueError("Invalid token payload.")

    try:
        user_id = int(subject)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid token subject.") from exc

    user = get_user_by_id(db, user_id)
    if user is None or not bool(user.is_active):
        raise ValueError("User not found or inactive.")
    return user
