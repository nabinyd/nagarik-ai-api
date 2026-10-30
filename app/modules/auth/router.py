from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.database.session import get_db
from app.modules.auth.schemas import (
    GoogleLoginRequest,
    GoogleLoginResponse,
)
from app.modules.auth.service import create_login_response, login_with_google

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/google",
    response_model=GoogleLoginResponse,
    status_code=status.HTTP_200_OK,
)
def google_login(
    payload: GoogleLoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> GoogleLoginResponse:
    """Verify Google ID token and create or retrieve the user."""
    user = login_with_google(db, payload.id_token)
    settings = get_settings()
    if settings.secret_key is None:
        raise AppError(
            "SECRET_KEY must be configured for authentication",
            status_code=500,
        )

    return create_login_response(
        user,
        settings.secret_key.get_secret_value(),
    )