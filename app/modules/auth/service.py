import re
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.modules.auth.google import verify_google_id_token
from app.modules.auth.models import User

ACCESS_TOKEN_EXPIRES_IN = 900
REFRESH_TOKEN_EXPIRES_IN = 60 * 60 * 24 * 30


def _create_token(user: User, secret: str, token_type: str, expires_in: int) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(user.id),
            "email": user.email,
            "type": token_type,
            "iat": now,
            "exp": now + timedelta(seconds=expires_in),
            "jti": str(uuid4()),
        },
        secret,
        algorithm="HS256",
    )


def _generate_username(db: Session, email: str) -> str:
    local_part = email.split("@", 1)[0].lower()

    # Allow only characters supported by your username convention.
    base = re.sub(r"[^a-z0-9_.-]", "", local_part)
    base = base.strip("._-")

    if len(base) < 3:
        base = f"user_{base}"

    base = base[:50]

    username = base
    counter = 1

    while db.scalar(
        select(User.id).where(User.username == username)
    ) is not None:
        suffix = f"_{counter}"
        username = f"{base[:50 - len(suffix)]}{suffix}"
        counter += 1

    return username


def login_with_google(db: Session, token: str) -> User:
    try:
        claims = verify_google_id_token(token)
    except ValueError as error:
        raise AppError(
            "Invalid or expired Google ID token",
            status_code=401,
        ) from error

    google_sub = claims["sub"]
    email = claims["email"].strip().lower()
    firstName = claims.get("given_name")
    lastName = claims.get("family_name")

    # The Google subject is the identity key, not the email.
    user = db.scalar(
        select(User).where(User.google_sub == google_sub)
    )

    if user is not None:
        user.email = email
        user.firstName = firstName
        user.lastName = lastName
        user.picture = claims.get("picture")

        try:
            db.commit()
            db.refresh(user)
        except IntegrityError as error:
            db.rollback()
            raise AppError(
                "Unable to update Google account",
                status_code=409,
            ) from error

        return user

    # Do not silently link a pre-existing password account by email.
    existing_email = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_email is not None:
        raise AppError(
            "An account with this email already exists. "
            "Sign in to that account and link Google securely.",
            status_code=409,
        )

    user = User(
        google_sub=google_sub,
        email=email,
        firstName=firstName,
        lastName=lastName,
        username=_generate_username(db, email),
        password_hash=None,
        picture=claims.get("picture"),
    )

    db.add(user)

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as error:
        db.rollback()

        # A concurrent login may have created the same Google user.
        user = db.scalar(
            select(User).where(User.google_sub == google_sub)
        )

        if user is not None:
            return user

        raise AppError(
            "Unable to create Google account. Please try again.",
            status_code=409,
        ) from error

    return user


def create_login_response(user: User, secret: str) -> dict:
    return {
        "user": user,
        "access_token": _create_token(
            user,
            secret,
            "access",
            ACCESS_TOKEN_EXPIRES_IN,
        ),
        "refresh_token": _create_token(
            user,
            secret,
            "refresh",
            REFRESH_TOKEN_EXPIRES_IN,
        ),
        "access_token_expires_in": ACCESS_TOKEN_EXPIRES_IN,
        "refresh_token_expires_in": REFRESH_TOKEN_EXPIRES_IN,
    }


def refresh_login(
    db: Session,
    refresh_token: str,
    secret: str,
) -> dict:
    try:
        payload = jwt.decode(
            refresh_token,
            secret,
            algorithms=["HS256"],
        )
        if payload.get("type") != "refresh":
            raise ValueError("Not a refresh token")
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as error:
        raise AppError(
            "Invalid or expired refresh token",
            status_code=401,
        ) from error

    user = db.get(User, user_id)
    if user is None:
        raise AppError(
            "User not found",
            status_code=401,
        )

    return create_login_response(user, secret)