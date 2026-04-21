from datetime import datetime, timedelta, timezone

from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User, UserSession

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30
COOKIE_NAME = "access_token"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str, session_id: str | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {"sub": user_id, "exp": expire}
    if session_id:
        payload["sid"] = session_id
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def _parse_user_agent(ua: str) -> tuple[str, str]:
    browser = "Unknown"
    os_name = "Unknown"

    if "Firefox/" in ua:
        browser = "Firefox"
    elif "Edg/" in ua:
        browser = "Microsoft Edge"
    elif "Chrome/" in ua:
        browser = "Google Chrome"
    elif "Safari/" in ua:
        browser = "Safari"

    if "Windows" in ua:
        os_name = "Windows"
    elif "Mac OS" in ua:
        os_name = "macOS"
    elif "Linux" in ua:
        os_name = "Linux"
    elif "Android" in ua:
        os_name = "Android"
    elif "iPhone" in ua or "iPad" in ua:
        os_name = "iOS"

    return browser, os_name


async def create_session(request: Request, user: User, db: AsyncSession) -> UserSession:
    ua = request.headers.get("user-agent", "")
    browser, os_name = _parse_user_agent(ua)
    ip = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or request.headers.get("x-real-ip", "")
        or (request.client.host if request.client else None)
    )

    session = UserSession(
        user_id=user.id,
        ip_address=ip,
        user_agent=ua,
        browser=browser,
        os=os_name,
    )
    db.add(session)
    await db.flush()
    return session


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user:
        user.last_active = datetime.now(timezone.utc)
        db.add(user)
        # Update session last_active
        sid = payload.get("sid")
        if sid:
            res = await db.execute(select(UserSession).where(UserSession.id == sid, UserSession.is_active.is_(True)))
            sess = res.scalar_one_or_none()
            if sess:
                sess.last_active = datetime.now(timezone.utc)
                db.add(sess)
            else:
                # Session was revoked
                return None
            # Store session_id on request for profile page
            request.state.session_id = sid
    return user


async def require_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await get_current_user(request, db)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=303, headers={"Location": f"/login?next={request.url.path}"})
    return user


async def require_admin(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await require_user(request, db)
    if not user.is_admin:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def set_auth_cookie(response, token: str):
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_DAYS * 86400,
    )


def clear_auth_cookie(response):
    response.delete_cookie(key=COOKIE_NAME)
