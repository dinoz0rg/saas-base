from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    hash_password, verify_password, create_access_token,
    set_auth_cookie, clear_auth_cookie, get_current_user,
    create_session, decode_token,
)
from app.database import get_db
from app.models.user import User, UserSession

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user: User | None = Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse("auth/login.html", {
        "request": request,
        "next": request.query_params.get("next", "/dashboard"),
    })


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str = Form("/dashboard"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "error": "Invalid email or password",
            "email": email,
            "next": next,
        }, status_code=400)

    # If 2FA is enabled, redirect to verification page
    if user.totp_enabled:
        # Store user_id temporarily in a short-lived cookie for 2FA verification
        from app.auth import COOKIE_NAME
        from jose import jwt
        from app.config import settings
        from app.auth import ALGORITHM
        from datetime import datetime, timedelta, timezone
        expire = datetime.now(timezone.utc) + timedelta(minutes=5)
        pending_token = jwt.encode({"sub": user.id, "exp": expire, "pending_2fa": True}, settings.SECRET_KEY, algorithm=ALGORITHM)
        response = RedirectResponse(url=f"/login/2fa?next={next}", status_code=303)
        response.set_cookie(key="pending_2fa", value=pending_token, httponly=True, samesite="lax", max_age=300)
        return response

    session = await create_session(request, user, db)
    token = create_access_token(user.id, session.id)
    response = RedirectResponse(url=next, status_code=303)
    set_auth_cookie(response, token)
    return response


@router.get("/login/2fa", response_class=HTMLResponse)
async def login_2fa_page(request: Request):
    pending = request.cookies.get("pending_2fa")
    if not pending:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("auth/login_2fa.html", {
        "request": request,
        "next": request.query_params.get("next", "/dashboard"),
    })


@router.post("/login/2fa")
async def login_2fa_submit(
    request: Request,
    code: str = Form(...),
    next: str = Form("/dashboard"),
    db: AsyncSession = Depends(get_db),
):
    import pyotp
    from jose import jwt, JWTError
    from app.config import settings
    from app.auth import ALGORITHM

    pending = request.cookies.get("pending_2fa")
    if not pending:
        return RedirectResponse(url="/login", status_code=303)

    try:
        payload = jwt.decode(pending, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if not payload.get("pending_2fa"):
            return RedirectResponse(url="/login", status_code=303)
        user_id = payload.get("sub")
    except JWTError:
        return RedirectResponse(url="/login", status_code=303)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.totp_secret:
        return RedirectResponse(url="/login", status_code=303)

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(code.strip(), valid_window=1):
        return templates.TemplateResponse("auth/login_2fa.html", {
            "request": request,
            "error": "Invalid verification code",
            "next": next,
        }, status_code=400)

    session = await create_session(request, user, db)
    token = create_access_token(user.id, session.id)
    response = RedirectResponse(url=next, status_code=303)
    set_auth_cookie(response, token)
    response.delete_cookie(key="pending_2fa")
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, user: User | None = Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse("auth/register.html", {"request": request})


@router.post("/register")
async def register_submit(
    request: Request,
    email: str = Form(...),
    display_name: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        return templates.TemplateResponse("auth/register.html", {
            "request": request,
            "error": "An account with this email already exists",
            "email": email,
            "display_name": display_name,
        }, status_code=400)

    if len(password) < 8:
        return templates.TemplateResponse("auth/register.html", {
            "request": request,
            "error": "Password must be at least 8 characters",
            "email": email,
            "display_name": display_name,
        }, status_code=400)

    user = User(
        email=email,
        display_name=display_name,
        hashed_password=hash_password(password),
    )
    db.add(user)
    await db.flush()

    session = await create_session(request, user, db)
    token = create_access_token(user.id, session.id)
    response = RedirectResponse(url="/dashboard", status_code=303)
    set_auth_cookie(response, token)
    return response


@router.get("/logout")
async def logout(request: Request, db: AsyncSession = Depends(get_db)):
    # Deactivate current session
    token = request.cookies.get("access_token")
    if token:
        payload = decode_token(token)
        if payload:
            sid = payload.get("sid")
            if sid:
                result = await db.execute(select(UserSession).where(UserSession.id == sid))
                sess = result.scalar_one_or_none()
                if sess:
                    sess.is_active = False
                    db.add(sess)

    response = RedirectResponse(url="/", status_code=303)
    clear_auth_cookie(response)
    return response
