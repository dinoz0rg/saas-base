from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, require_user, verify_password, hash_password
from app.database import get_db
from app.models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


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
            return templates.TemplateResponse("profile.html", {
                "request": request, "user": user, "error": "Email already in use",
                "active_page": "profile",
            }, status_code=400)

    user.display_name = display_name
    user.email = email
    await db.flush()

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
    ctx = {
        "request": request, "user": user,
        "active_page": "profile",
    }

    if not verify_password(current_password, user.hashed_password):
        return templates.TemplateResponse("profile.html", {**ctx, "error": "Current password is incorrect"}, status_code=400)

    if len(new_password) < 8:
        return templates.TemplateResponse("profile.html", {**ctx, "error": "New password must be at least 8 characters"}, status_code=400)

    user.hashed_password = hash_password(new_password)
    await db.flush()

    return templates.TemplateResponse("profile.html", {**ctx, "success": "Password updated"})
