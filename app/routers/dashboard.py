from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_user
from app.database import get_db
from app.models.workspace import Activity, Metric, Page
from app.models.user import User

router = APIRouter(prefix="/dashboard")
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
async def overview(
    request: Request,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    # Recent activities
    result = await db.execute(
        select(Activity)
        .where(Activity.user_id == user.id)
        .order_by(Activity.created_at.desc())
        .limit(10)
    )
    activities = result.scalars().all()

    # Stats
    page_count = (await db.execute(
        select(func.count(Page.id)).where(Page.user_id == user.id)
    )).scalar() or 0

    total_views = (await db.execute(
        select(func.coalesce(func.sum(Page.views_count), 0)).where(Page.user_id == user.id)
    )).scalar() or 0

    activity_count = (await db.execute(
        select(func.count(Activity.id)).where(Activity.user_id == user.id)
    )).scalar() or 0

    published_count = (await db.execute(
        select(func.count(Page.id)).where(Page.user_id == user.id, Page.is_published == True)
    )).scalar() or 0

    stats = [
        {"label": "Total Views", "value": f"{total_views:,}", "icon": "eye", "color": "blue", "change": 12},
        {"label": "Published", "value": str(published_count), "icon": "doc", "color": "emerald", "change": 8},
        {"label": "Pages", "value": str(page_count), "icon": "doc", "color": "violet", "change": 3},
        {"label": "Actions", "value": str(activity_count), "icon": "bolt", "color": "amber", "change": 24},
    ]

    # Top pages
    result = await db.execute(
        select(Page)
        .where(Page.user_id == user.id)
        .order_by(Page.views_count.desc())
        .limit(5)
    )
    top_pages = result.scalars().all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "activities": activities,
        "stats": stats,
        "top_pages": top_pages,
        "active_page": "overview",
    })


@router.get("/analytics", response_class=HTMLResponse)
async def analytics(
    request: Request,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Metric)
        .where(Metric.user_id == user.id)
        .order_by(Metric.recorded_at.desc())
        .limit(100)
    )
    metrics = result.scalars().all()

    result = await db.execute(
        select(Page)
        .where(Page.user_id == user.id)
        .order_by(Page.views_count.desc())
    )
    pages = result.scalars().all()

    total_views = sum(p.views_count for p in pages)
    published_count = sum(1 for p in pages if p.is_published)

    return templates.TemplateResponse("page_dashboard.html", {
        "request": request,
        "user": user,
        "active_page": "analytics",
        "page_title": "Analytics",
        "page_description": "Usage metrics and insights for your account.",
        "metrics": metrics,
        "pages": pages,
        "total_views": total_views,
        "published_count": published_count,
    })


@router.get("/activity", response_class=HTMLResponse)
async def activity_log(
    request: Request,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Activity)
        .where(Activity.user_id == user.id)
        .order_by(Activity.created_at.desc())
        .limit(50)
    )
    activities = result.scalars().all()

    return templates.TemplateResponse("page_dashboard.html", {
        "request": request,
        "user": user,
        "active_page": "activity",
        "page_title": "Activity",
        "page_description": "All recent activity on your account.",
        "activities": activities,
    })


@router.get("/pages", response_class=HTMLResponse)
async def pages_list(
    request: Request,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Page)
        .where(Page.user_id == user.id)
        .order_by(Page.updated_at.desc())
    )
    pages = result.scalars().all()

    return templates.TemplateResponse("page_dashboard.html", {
        "request": request,
        "user": user,
        "active_page": "pages",
        "page_title": "Pages",
        "page_description": "Manage your content pages.",
        "pages": pages,
    })


@router.get("/reports", response_class=HTMLResponse)
async def reports(
    request: Request,
    user: User = Depends(require_user),
):
    return templates.TemplateResponse("page_dashboard.html", {
        "request": request,
        "user": user,
        "active_page": "reports",
        "page_title": "Reports",
        "page_description": "Generate and view reports.",
        "empty_message": "Reports will be available as your usage grows.",
    })


@router.get("/settings", response_class=HTMLResponse)
async def settings(
    request: Request,
    user: User = Depends(require_user),
):
    return templates.TemplateResponse("page_dashboard.html", {
        "request": request,
        "user": user,
        "active_page": "settings",
        "page_title": "Settings",
        "page_description": "Configure your account.",
        "settings_items": [
            {"title": "General", "subtitle": "Display name, email, and preferences", "icon": "⚙"},
            {"title": "Billing", "subtitle": "Plans, payment methods, and invoices", "icon": "💳"},
            {"title": "API Keys", "subtitle": "Manage API access tokens", "icon": "🔑"},
            {"title": "Integrations", "subtitle": "Connect with other tools", "icon": "🔗"},
            {"title": "Danger Zone", "subtitle": "Delete account", "icon": "⚠️"},
        ],
    })


@router.get("/pricing", response_class=HTMLResponse)
async def pricing(
    request: Request,
    user: User = Depends(require_user),
):
    return templates.TemplateResponse("page_dashboard.html", {
        "request": request,
        "user": user,
        "active_page": "pricing",
        "page_title": "Pricing",
        "page_description": "Choose the plan that fits your needs.",
    })
