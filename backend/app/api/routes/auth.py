import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_manager
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, TokenResponse, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/api/auth",
    )


async def _issue_tokens(user: User, db: AsyncSession, response: Response) -> LoginResponse:
    jti = uuid.uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    db.add(RefreshToken(jti=jti, user_id=user.id, expires_at=expires_at))
    await db.commit()

    access_token = create_access_token(user_id=str(user.id), role=user.role)
    refresh_token = create_refresh_token(user_id=str(user.id), jti=str(jti))
    _set_refresh_cookie(response, refresh_token)

    return LoginResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserOut.model_validate(user),
    )


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)) -> LoginResponse:
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return await _issue_tokens(user, db, response)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    raw = request.cookies.get(REFRESH_COOKIE_NAME)
    if raw is None:
        raise HTTPException(status_code=401, detail="No refresh token")

    try:
        payload = decode_token(raw)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    try:
        jti = uuid.UUID(payload["jti"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    record = await db.get(RefreshToken, jti)

    if record is None or record.revoked or record.expires_at < datetime.now(timezone.utc):
        if record is not None:
            # Reuse of an already-revoked/expired jti — treat as possible token
            # theft and revoke every active session for this user.
            await db.execute(
                update(RefreshToken).where(RefreshToken.user_id == record.user_id).values(revoked=True)
            )
            await db.commit()
        raise HTTPException(status_code=401, detail="Refresh token invalid or revoked")

    user = await db.get(User, record.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    record.revoked = True
    new_jti = uuid.uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    db.add(RefreshToken(jti=new_jti, user_id=user.id, expires_at=expires_at))
    await db.commit()

    access_token = create_access_token(user_id=str(user.id), role=user.role)
    new_refresh_token = create_refresh_token(user_id=str(user.id), jti=str(new_jti))
    _set_refresh_cookie(response, new_refresh_token)

    return TokenResponse(access_token=access_token, expires_in=settings.access_token_expire_minutes * 60)


@router.post("/logout", status_code=204)
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)) -> None:
    raw = request.cookies.get(REFRESH_COOKIE_NAME)
    if raw:
        try:
            payload = decode_token(raw)
            if payload.get("type") == "refresh":
                jti = uuid.UUID(payload["jti"])
                record = await db.get(RefreshToken, jti)
                if record is not None:
                    record.revoked = True
                    await db.commit()
        except (jwt.PyJWTError, KeyError, ValueError):
            pass  # already-invalid cookie — nothing to revoke, still clear it below
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/api/auth")


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_manager)) -> UserOut:
    return UserOut.model_validate(current_user)
