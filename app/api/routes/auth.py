from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.security import create_access_token, get_password_hash, verify_password
from app.core.config import settings
from app.core.google_oauth import verify_google_token
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserRead, TokenResponse, GoogleTokenRequest, ProfileUpdateRequest
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserRead)
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        existing = db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        user = User(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=get_password_hash(payload.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user.lockout_until and user.lockout_until > datetime.utcnow():
        remaining = int((user.lockout_until - datetime.utcnow()).total_seconds() / 60) or 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account locked. Try again in {remaining} minute(s).",
        )

    if not verify_password(payload.password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.max_login_attempts:
            user.lockout_until = datetime.utcnow() + timedelta(minutes=settings.lockout_minutes)
            user.failed_login_attempts = 0
        db.add(user)
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user.failed_login_attempts = 0
    user.lockout_until = None
    db.add(user)
    db.commit()

    token = create_access_token(subject=user.email)
    return TokenResponse(access_token=token)


@router.post("/google", response_model=TokenResponse)
async def google_login(payload: GoogleTokenRequest, db: Session = Depends(get_db)):
    """
    Google OAuth login endpoint.
    Verify Google ID token and create/login user.
    """
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google OAuth not configured",
        )

    # Verify token
    claims = await verify_google_token(payload.token)
    if not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        )

    email = claims.get("email")
    google_id = claims.get("sub")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not available in Google token",
        )

    full_name = claims.get("name")

    # Find or create user
    user = db.query(User).filter(User.email == email).first()

    if not user:
        # Create new user from Google
        user = User(
            email=email,
            full_name=full_name,
            oauth_provider="google",
            oauth_id=google_id,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update existing user with Google OAuth info if they didn't have it
        if not user.oauth_provider:
            user.oauth_provider = "google"
            user.oauth_id = google_id
        if not user.full_name and full_name:
            user.full_name = full_name
            db.add(user)
            db.commit()

    # Reset lockout if any
    if user.lockout_until and user.lockout_until < datetime.utcnow():
        user.lockout_until = None
        user.failed_login_attempts = 0
        db.add(user)
        db.commit()

    # Create JWT token
    token = create_access_token(subject=user.email)
    return TokenResponse(access_token=token)


@router.put("/me", response_model=UserRead)
def update_me(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.full_name = payload.full_name.strip()

    if payload.password:
        current_user.hashed_password = get_password_hash(payload.password)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user

