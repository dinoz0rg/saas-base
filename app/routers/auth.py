from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    hash_password, verify_password, create_access_token,
    set_auth_cookie, clear_auth_cookie, get_current_user,
)
from app.database import get_db
from app.models.user import User

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

    token = create_access_token(user.id)
    response = RedirectResponse(url=next, status_code=303)
    set_auth_cookie(response, token)
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
    # Check if email already taken
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

    token = create_access_token(user.id)
    response = RedirectResponse(url="/dashboard", status_code=303)
    set_auth_cookie(response, token)
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    clear_auth_cookie(response)
    return response
