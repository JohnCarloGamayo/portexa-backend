"""Google OAuth token verification utilities"""
from typing import Optional

import httpx

from app.core.config import settings


async def verify_google_token(token: str) -> Optional[dict]:
    """Verify Google ID token and return validated claims."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": token},
                timeout=10.0,
            )

        if response.status_code != 200:
            return None

        claims = response.json()

        # Token must be issued for this OAuth client.
        if claims.get("aud") != settings.google_client_id:
            return None

        # Issuer must be Google accounts.
        if claims.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
            return None

        # Enforce verified email for account linkage.
        email_verified = claims.get("email_verified")
        if email_verified not in {True, "true"}:
            return None

        return claims
    except Exception:
        return None
