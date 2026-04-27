"""
Settings router — full account & workspace settings backed by the User and
ApiKey models. Renders one tabbed page (`settings.html`) and exposes JSON
endpoints for in-page form submissions.
"""
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    require_user, verify_password, hash_password, clear_auth_cookie,
)
from app.database import get_db
from app.models.user import User, UserSession
from app.models.workspace import ApiKey

router = APIRouter(prefix="/dashboard/settings")
templates = Jinja2Templates(directory="app/templates")


# Languages and timezones surfaced in the UI dropdowns.
LANGUAGES = [
    ("en", "English"), ("es", "Español"), ("fr", "Français"),
    ("de", "Deutsch"), ("pt", "Português"), ("ja", "日本語"),
    ("zh", "中文"),
]
TIMEZONES = [
    "UTC", "Europe/London", "Europe/Berlin", "Europe/Paris",
    "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles",
    "Asia/Tokyo", "Asia/Shanghai", "Asia/Kolkata", "Australia/Sydney",
]
THEMES = ["system", "light", "dark"]
ACCENTS = ["blue", "violet", "emerald", "orange", "rose", "neutral"]
DENSITIES = ["comfortable", "compact"]


# ── Page render ─────────────────────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    tab = request.query_params.get("tab", "general")
    if tab not in {"general", "appearance", "notifications", "security",
                   "sessions", "api-keys", "billing", "danger"}:
        tab = "general"

    keys_res = await db.execute(
        select(ApiKey).where(ApiKey.user_id == user.id, ApiKey.revoked.is_(False))
        .order_by(ApiKey.created_at.desc())
    )
    api_keys = keys_res.scalars().all()

    return templates.TemplateResponse("settings.html", {
        "request": request,
        "user": user,
        "active_page": "settings",
        "tab": tab,
        "languages": LANGUAGES,
        "timezones": TIMEZONES,
        "themes": THEMES,
        "accents": ACCENTS,
        "densities": DENSITIES,
        "api_keys": api_keys,
    })


def _ok(extra: dict | None = None):
    payload = {"ok": True}
    if extra:
        payload.update(extra)
    return JSONResponse(payload)


def _err(msg: str, status: int = 400):
    return JSONResponse({"ok": False, "error": msg}, status_code=status)


# ── General ─────────────────────────────────────────────────────────────────

@router.post("/general")
async def save_general(
    display_name: str = Form(...),
    email: str = Form(...),
    workspace_name: str = Form(""),
    bio: str = Form(""),
    language: str = Form("en"),
    timezone: str = Form("UTC"),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    display_name = display_name.strip()
    email = email.strip().lower()
    if not display_name or len(display_name) > 100:
        return _err("Display name is required (max 100 chars).")
    if "@" not in email or len(email) > 255:
        return _err("Please enter a valid email address.")

    if email != user.email:
        existing = await db.execute(select(User).where(User.email == email, User.id != user.id))
        if existing.scalar_one_or_none():
            return _err("That email is already in use.")

    if language not in {code for code, _ in LANGUAGES}:
        return _err("Unsupported language.")
    if timezone not in TIMEZONES:
        return _err("Unsupported timezone.")

    user.display_name = display_name
    user.email = email
    user.workspace_name = workspace_name.strip() or None
    user.bio = (bio or "").strip()[:1000] or None
    user.language = language
    user.timezone = timezone
    await db.flush()
    return _ok()


# ── Appearance ──────────────────────────────────────────────────────────────

@router.post("/appearance")
async def save_appearance(
    theme: str = Form(...),
    accent: str = Form(...),
    density: str = Form("comfortable"),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    if theme not in THEMES:
        return _err("Invalid theme.")
    if accent not in ACCENTS:
        return _err("Invalid accent.")
    if density not in DENSITIES:
        return _err("Invalid density.")
    user.theme = theme
    user.accent = accent
    user.density = density
    await db.flush()
    return _ok({"theme": theme, "accent": accent, "density": density})


# ── Notifications ───────────────────────────────────────────────────────────

@router.post("/notifications")
async def save_notifications(
    notify_product: str = Form(""),
    notify_security: str = Form(""),
    notify_marketing: str = Form(""),
    notify_weekly_digest: str = Form(""),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    truthy = {"on", "true", "1", "yes"}
    user.notify_product = notify_product.lower() in truthy
    user.notify_security = notify_security.lower() in truthy
    user.notify_marketing = notify_marketing.lower() in truthy
    user.notify_weekly_digest = notify_weekly_digest.lower() in truthy
    await db.flush()
    return _ok()


# ── Security: password ──────────────────────────────────────────────────────

@router.post("/password")
async def change_password(
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(current_password, user.hashed_password):
        return _err("Current password is incorrect.")
    if new_password != confirm_password:
        return _err("New passwords don't match.")
    if len(new_password) < 8:
        return _err("Password must be at least 8 characters.")
    if new_password == current_password:
        return _err("New password must be different from the current one.")
    user.hashed_password = hash_password(new_password)
    await db.flush()
    return _ok()


# ── API keys ────────────────────────────────────────────────────────────────

@router.post("/api-keys")
async def create_api_key(
    name: str = Form(...),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    name = name.strip()
    if not name or len(name) > 100:
        return _err("Name is required (max 100 chars).")
    raw = "sk_live_" + secrets.token_urlsafe(32)
    prefix = raw[:12]
    key = ApiKey(
        user_id=user.id,
        name=name,
        prefix=prefix,
        hashed_key=hash_password(raw),
    )
    db.add(key)
    await db.flush()
    return _ok({
        "id": key.id, "name": key.name, "prefix": prefix,
        "key": raw,  # shown only once
        "created_at": key.created_at.isoformat(),
    })


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user.id)
    )
    key = res.scalar_one_or_none()
    if not key:
        return _err("API key not found.", 404)
    key.revoked = True
    await db.flush()
    return _ok()


# ── Billing (mock) ──────────────────────────────────────────────────────────

@router.post("/billing/subscribe")
async def subscribe(
    plan: str = Form(...),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    if plan not in {"free", "pro", "enterprise"}:
        return _err("Unknown plan.")
    user.subscription_tier = plan
    await db.flush()
    return _ok({"plan": plan})


# ── Danger zone ─────────────────────────────────────────────────────────────

@router.post("/danger/delete")
async def delete_account(
    password: str = Form(...),
    confirm: str = Form(""),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(password, user.hashed_password):
        return _err("Incorrect password.")
    if confirm.strip().upper() != "DELETE":
        return _err('Type "DELETE" to confirm.')

    # Cascade-clean owned data.
    user_id = user.id
    await db.execute(delete(UserSession).where(UserSession.user_id == user_id))
    await db.execute(delete(ApiKey).where(ApiKey.user_id == user_id))
    await db.delete(user)
    await db.flush()
    response = JSONResponse({"ok": True, "redirect": "/"})
    clear_auth_cookie(response)
    return response
