from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import timedelta
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.core.database import get_db
from app.core import security, config
from app.models.user import User

from app.api import deps

router = APIRouter(prefix="/auth", tags=["Auth"])


def _build_token_response(user):
    """Shared helper to build a JWT token response for a user."""
    access_token_expires = timedelta(minutes=config.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": str(user.id), "role": user.role}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id,
        "name": user.name,
        "surname": user.surname,
        "image": user.image,
    }


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # form_data.username will be the email
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _build_token_response(user)


class GoogleSSORequest(BaseModel):
    credential: str  # Google ID token from GSI


@router.post("/sso")
def sso_login(payload: GoogleSSORequest, db: Session = Depends(get_db)):
    """Google SSO login — verify Google ID token, match email to user, issue JWT."""
    try:
        idinfo = id_token.verify_oauth2_token(
            payload.credential,
            google_requests.Request(),
            config.settings.GOOGLE_CLIENT_ID,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        )

    email = idinfo.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google account has no email",
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Email {email} not found in system",
        )

    return _build_token_response(user)


@router.get("/google-client-id")
def get_google_client_id():
    """Return the Google Client ID for frontend GSI initialization."""
    return {"client_id": config.settings.GOOGLE_CLIENT_ID}
