from __future__ import annotations

from uuid import uuid4
import httpx
from fastapi import Cookie, Depends, Header
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_session
from app.core.errors import UnauthorizedError
from app.schemas.common import UserContext


def get_db(session: Session = Depends(get_session)) -> Session:
    return session


def get_current_user(
    ecosystem_session: str | None = Cookie(default=None),
    x_user_id: str | None = Header(default=None),
    x_username: str | None = Header(default=None),
    x_display_name: str | None = Header(default=None),
    x_user_email: str | None = Header(default=None),
    x_platform_admin: str | None = Header(default=None),
) -> UserContext:
    settings = get_settings()
    if x_user_id:
        return UserContext(user_id=x_user_id, username=x_username or x_user_id, display_name=x_display_name or x_username or x_user_id, email=x_user_email, is_platform_admin=x_platform_admin == "1")
    if ecosystem_session:
        try:
            response = httpx.post(f"{settings.identity_internal_url.rstrip('/')}/session-exchange", cookies={"ecosystem_session": ecosystem_session}, timeout=2.5)
            if response.status_code == 200:
                payload = response.json()
                return UserContext(
                    user_id=payload["subject_id"],
                    username=payload.get("username") or payload.get("email") or payload["subject_id"],
                    display_name=payload.get("display_name") or payload.get("username") or payload.get("email") or payload["subject_id"],
                    email=payload.get("email"),
                    is_platform_admin=bool(payload.get("is_platform_admin")) or x_platform_admin == "1",
                )
        except httpx.HTTPError:
            pass
    if settings.allow_dev_auth:
        return UserContext(user_id="usr_dev_karpik", username="karpik", display_name="karpik", email="karpik@local.dev", is_platform_admin=x_platform_admin == "1")
    raise UnauthorizedError("Authentication required")


def get_request_id(x_request_id: str | None = Header(default=None)) -> str:
    return x_request_id or str(uuid4())
