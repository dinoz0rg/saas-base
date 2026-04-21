import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, require_user, verify_password, hash_password
from app.database import get_db
from app.models.user import User

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


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    user: User = Depends(require_user),
):
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user,
        "active_page": "profile",
    })


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
