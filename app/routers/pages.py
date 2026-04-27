import uuid
import io
import base64
from pathlib import Path

import pyotp
import qrcode
from fastapi import APIRouter, Depends, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    get_current_user, require_user, verify_password, hash_password,
    create_access_token, set_auth_cookie, create_session, decode_token,
)
from app.database import get_db
from app.models.user import User, UserSession

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@router.get("/", response_class=HTMLResponse)
async def landing(request: Request, user: User | None = Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse("landing.html", {"request": request, "user": user})


@router.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request, user: User | None = Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/dashboard/pricing", status_code=303)
    return templates.TemplateResponse("pricing.html", {"request": request, "user": user})


@router.get("/profile")
async def profile_page(request: Request):
    # /profile and /settings were merged; keep this as a permanent redirect so
    # any existing links/bookmarks land on the unified settings surface.
    return RedirectResponse(url="/settings", status_code=303)


def _wants_json(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "application/json" in accept


@router.post("/profile")
async def profile_update(
    request: Request,
    display_name: str = Form(...),
    email: str = Form(...),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    if email != user.email:
        existing = await db.execute(select(User).where(User.email == email, User.id != user.id))
        if existing.scalar_one_or_none():
            if _wants_json(request):
                return JSONResponse({"ok": False, "error": "Email already in use"}, status_code=400)
            return templates.TemplateResponse("profile.html", {
                "request": request, "user": user, "error": "Email already in use",
                "active_page": "profile",
            }, status_code=400)

    user.display_name = display_name
    user.email = email
    await db.flush()

    if _wants_json(request):
        return JSONResponse({"ok": True})

    return templates.TemplateResponse("profile.html", {
        "request": request, "user": user, "success": "Profile updated",
        "active_page": "profile",
    })


@router.post("/profile/password")
async def profile_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(current_password, user.hashed_password):
        if _wants_json(request):
            return JSONResponse({"ok": False, "error": "Current password is incorrect"}, status_code=400)
        return templates.TemplateResponse("profile.html", {
            "request": request, "user": user, "error": "Current password is incorrect",
            "active_page": "profile",
        }, status_code=400)

    if len(new_password) < 8:
        if _wants_json(request):
            return JSONResponse({"ok": False, "error": "New password must be at least 8 characters"}, status_code=400)
        return templates.TemplateResponse("profile.html", {
            "request": request, "user": user, "error": "New password must be at least 8 characters",
            "active_page": "profile",
        }, status_code=400)

    user.hashed_password = hash_password(new_password)
    await db.flush()

    if _wants_json(request):
        return JSONResponse({"ok": True})

    return templates.TemplateResponse("profile.html", {
        "request": request, "user": user, "success": "Password updated",
        "active_page": "profile",
    })


@router.post("/profile/avatar")
async def profile_avatar(
    request: Request,
    avatar: UploadFile = File(...),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    # Validate content type
    if not avatar.content_type or not avatar.content_type.startswith("image/"):
        return JSONResponse({"ok": False, "error": "File must be an image"}, status_code=400)

    # Read and validate size (2MB)
    data = await avatar.read()
    if len(data) > 2 * 1024 * 1024:
        return JSONResponse({"ok": False, "error": "File too large. Maximum size is 2MB."}, status_code=400)

    # Save file to /static/uploads/profile/<userId>/
    ext = Path(avatar.filename).suffix if avatar.filename else ".png"
    filename = f"{uuid.uuid4().hex}{ext}"
    user_dir = STATIC_DIR / "uploads" / "profile" / str(user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    filepath = user_dir / filename
    filepath.write_bytes(data)

    # Delete old avatar file if it exists
    if user.avatar_url:
        old_path = STATIC_DIR / user.avatar_url.lstrip("/").replace("static/", "", 1)
        if old_path.exists():
            old_path.unlink(missing_ok=True)

    user.avatar_url = f"/static/uploads/profile/{user.id}/{filename}"
    await db.flush()

    return JSONResponse({"ok": True, "avatar_url": user.avatar_url})


# ── 2FA Endpoints ──

@router.post("/profile/2fa/setup")
async def setup_2fa(
    request: Request,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    secret = pyotp.random_base32()
    user.totp_secret = secret
    await db.flush()

    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(name=user.email, issuer_name="Aceternity")

    # Generate QR code as base64
    img = qrcode.make(provisioning_uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    return JSONResponse({
        "ok": True,
        "secret": secret,
        "qr_code": f"data:image/png;base64,{qr_b64}",
    })


@router.post("/profile/2fa/verify")
async def verify_2fa(
    request: Request,
    code: str = Form(...),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.totp_secret:
        return JSONResponse({"ok": False, "error": "2FA not set up"}, status_code=400)

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(code.strip(), valid_window=1):
        return JSONResponse({"ok": False, "error": "Invalid code. Please try again."}, status_code=400)

    user.totp_enabled = True
    await db.flush()
    return JSONResponse({"ok": True})


@router.post("/profile/2fa/disable")
async def disable_2fa(
    request: Request,
    password: str = Form(...),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(password, user.hashed_password):
        return JSONResponse({"ok": False, "error": "Incorrect password"}, status_code=400)

    user.totp_secret = None
    user.totp_enabled = False
    await db.flush()
    return JSONResponse({"ok": True})


# ── Session Endpoints ──

@router.get("/api/sessions")
async def list_sessions(
    request: Request,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserSession)
        .where(UserSession.user_id == user.id, UserSession.is_active.is_(True))
        .order_by(UserSession.last_active.desc())
    )
    sessions = result.scalars().all()

    current_sid = getattr(request.state, "session_id", None)

    data = []
    for s in sessions:
        data.append({
            "id": s.id,
            "browser": s.browser or "Unknown",
            "os": s.os or "Unknown",
            "ip_address": s.ip_address or "Unknown",
            "last_active": s.last_active.isoformat() if s.last_active else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "is_current": s.id == current_sid,
        })

    return JSONResponse({"ok": True, "sessions": data})


@router.delete("/api/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    request: Request,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == user.id,
            UserSession.is_active.is_(True),
        )
    )
    sess = result.scalar_one_or_none()
    if not sess:
        return JSONResponse({"ok": False, "error": "Session not found"}, status_code=404)

    sess.is_active = False
    db.add(sess)
    await db.flush()
    return JSONResponse({"ok": True})


@router.post("/api/sessions/revoke-others")
async def revoke_other_sessions(
    request: Request,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    current_sid = getattr(request.state, "session_id", None)
    await db.execute(
        update(UserSession)
        .where(
            UserSession.user_id == user.id,
            UserSession.is_active.is_(True),
            UserSession.id != current_sid,
        )
        .values(is_active=False)
    )
    await db.flush()
    return JSONResponse({"ok": True})
