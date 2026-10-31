import os

from google.auth.transport.requests import Request
from google.oauth2 import id_token
from app.core.config import get_settings


GOOGLE_CLIENT_ID = get_settings().google_client_id

_google_request = Request()


def verify_google_id_token(token: str) -> dict:
    if not GOOGLE_CLIENT_ID:
        raise RuntimeError("GOOGLE_CLIENT_ID is not configured")

    claims = id_token.verify_oauth2_token(
        token,
        _google_request,
        GOOGLE_CLIENT_ID,
    )

    if claims.get("iss") not in {
        "accounts.google.com",
        "https://accounts.google.com",
    }:
        raise ValueError("Invalid Google token issuer")

    if not claims.get("sub"):
        raise ValueError("Google account ID is missing")

    if not claims.get("email"):
        raise ValueError("Email is missing")

    if claims.get("email_verified") is not True:
        raise ValueError("Google email is not verified")

    return claims