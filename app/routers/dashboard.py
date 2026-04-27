import re
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_user, require_admin
from app.database import get_db
from app.models.account import Activity, Metric, Page
from app.models.user import User

router = APIRouter(prefix="/dashboard")
templates = Jinja2Templates(directory="app/templates")


def _slugify(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:80] or "untitled"


# ── Overview ────────────────────────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
async def overview(
    request: Request,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Activity).where(Activity.user_id == user.id)
        .order_by(Activity.created_at.desc()).limit(10)
    )
    activities = result.scalars().all()

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
        select(func.count(Page.id)).where(Page.user_id == user.id, Page.is_published == True)  # noqa: E712
    )).scalar() or 0

    stats = [
        {"label": "Total Views", "value": f"{total_views:,}", "icon": "eye", "bg": "rgb(66, 242, 114)", "change": 12},
        {"label": "Published", "value": str(published_count), "icon": "doc", "bg": "rgb(130, 252, 78)", "change": 8},
        {"label": "Pages", "value": str(page_count), "icon": "doc", "bg": "rgb(210, 252, 67)", "change": 3},
        {"label": "Actions", "value": str(activity_count), "icon": "bolt", "bg": "rgb(250, 240, 60)", "change": 24},
    ]

    result = await db.execute(
        select(Page).where(Page.user_id == user.id).order_by(Page.views_count.desc()).limit(5)
    )
    top_pages = result.scalars().all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request, "user": user, "activities": activities,
        "stats": stats, "top_pages": top_pages, "active_page": "overview",
    })


# ── Analytics (admin) ───────────────────────────────────────────────────────

@router.get("/analytics", response_class=HTMLResponse)
async def analytics(
    request: Request,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    metrics = (await db.execute(select(Metric).order_by(Metric.recorded_at.desc()).limit(100))).scalars().all()
    pages = (await db.execute(select(Page).order_by(Page.views_count.desc()))).scalars().all()
    total_views = sum(p.views_count for p in pages)
    published_count = sum(1 for p in pages if p.is_published)
    user_count = (await db.execute(select(func.count(User.id)))).scalar() or 0

    return templates.TemplateResponse("page_dashboard.html", {
        "request": request, "user": user, "active_page": "analytics",
        "page_title": "Analytics",
        "page_description": "Aggregated usage metrics and insights across all users.",
        "metrics": metrics, "pages": pages,
        "total_views": total_views, "published_count": published_count,
        "user_count": user_count,
    })


# ── Activity (admin) ────────────────────────────────────────────────────────

@router.get("/activity", response_class=HTMLResponse)
async def activity_log(
    request: Request,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    activities = (await db.execute(
        select(Activity).order_by(Activity.created_at.desc()).limit(50)
    )).scalars().all()
    return templates.TemplateResponse("page_dashboard.html", {
        "request": request, "user": user, "active_page": "activity",
        "page_title": "Activity",
        "page_description": "Recent activity across all users.",
        "activities": activities,
    })


# ── Pages: list + CRUD ──────────────────────────────────────────────────────

@router.get("/pages", response_class=HTMLResponse)
async def pages_list(
    request: Request,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    pages = (await db.execute(
        select(Page).where(Page.user_id == user.id).order_by(Page.updated_at.desc())
    )).scalars().all()
    return templates.TemplateResponse("pages.html", {
        "request": request, "user": user, "active_page": "pages",
        "pages": pages,
    })


@router.get("/pages/new", response_class=HTMLResponse)
async def new_page(
    request: Request,
    user: User = Depends(require_user),
):
    return templates.TemplateResponse("page_editor.html", {
        "request": request, "user": user, "active_page": "pages",
        "page": None,
    })


@router.post("/pages")
async def create_page(
    title: str = Form(...),
    slug: str = Form(""),
    content: str = Form(""),
    is_published: str = Form(""),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    title = title.strip()
    if not title:
        return JSONResponse({"ok": False, "error": "Title is required."}, status_code=400)
    slug_value = _slugify(slug or title)
    page = Page(
        user_id=user.id,
        title=title[:200],
        slug=slug_value,
        content=content or None,
        is_published=is_published.lower() in {"on", "true", "1"},
    )
    db.add(page)
    await db.flush()
    return JSONResponse({"ok": True, "id": page.id, "redirect": f"/dashboard/pages/{page.id}/edit"})


@router.get("/pages/{page_id}/edit", response_class=HTMLResponse)
async def edit_page(
    page_id: str,
    request: Request,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Page).where(Page.id == page_id, Page.user_id == user.id))
    page = res.scalar_one_or_none()
    if not page:
        return RedirectResponse(url="/dashboard/pages", status_code=303)
    return templates.TemplateResponse("page_editor.html", {
        "request": request, "user": user, "active_page": "pages", "page": page,
    })


@router.post("/pages/{page_id}")
async def update_page(
    page_id: str,
    title: str = Form(...),
    slug: str = Form(""),
    content: str = Form(""),
    is_published: str = Form(""),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Page).where(Page.id == page_id, Page.user_id == user.id))
    page = res.scalar_one_or_none()
    if not page:
        return JSONResponse({"ok": False, "error": "Page not found."}, status_code=404)
    title = title.strip()
    if not title:
        return JSONResponse({"ok": False, "error": "Title is required."}, status_code=400)
    page.title = title[:200]
    page.slug = _slugify(slug or title)
    page.content = content or None
    page.is_published = is_published.lower() in {"on", "true", "1"}
    await db.flush()
    return JSONResponse({"ok": True})


@router.post("/pages/{page_id}/delete")
async def delete_page(
    page_id: str,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Page).where(Page.id == page_id, Page.user_id == user.id))
    page = res.scalar_one_or_none()
    if not page:
        return JSONResponse({"ok": False, "error": "Page not found."}, status_code=404)
    await db.delete(page)
    await db.flush()
    return JSONResponse({"ok": True})


@router.post("/pages/{page_id}/publish")
async def toggle_publish(
    page_id: str,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Page).where(Page.id == page_id, Page.user_id == user.id))
    page = res.scalar_one_or_none()
    if not page:
        return JSONResponse({"ok": False, "error": "Page not found."}, status_code=404)
    page.is_published = not page.is_published
    await db.flush()
    return JSONResponse({"ok": True, "is_published": page.is_published})


# ── Reports ─────────────────────────────────────────────────────────────────

@router.get("/reports", response_class=HTMLResponse)
async def reports(
    request: Request,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    pages = (await db.execute(
        select(Page).where(Page.user_id == user.id).order_by(Page.views_count.desc())
    )).scalars().all()

    total_views = sum(p.views_count for p in pages)
    published_count = sum(1 for p in pages if p.is_published)
    draft_count = len(pages) - published_count

    # Activity counts in the last 30 days, bucketed per day for a sparkline.
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    activities = (await db.execute(
        select(Activity).where(
            Activity.user_id == user.id, Activity.created_at >= cutoff
        ).order_by(Activity.created_at.asc())
    )).scalars().all()

    buckets = {(cutoff.date() + timedelta(days=i)).isoformat(): 0 for i in range(31)}
    breakdown: dict[str, int] = {}
    for a in activities:
        key = a.created_at.date().isoformat()
        if key in buckets:
            buckets[key] += 1
        breakdown[a.action.value] = breakdown.get(a.action.value, 0) + 1

    sparkline = list(buckets.values())

    return templates.TemplateResponse("reports.html", {
        "request": request, "user": user, "active_page": "reports",
        "pages": pages, "total_views": total_views,
        "published_count": published_count, "draft_count": draft_count,
        "activity_count": len(activities), "sparkline": sparkline,
        "breakdown": sorted(breakdown.items(), key=lambda x: -x[1]),
    })


# ── Tests / Pricing (placeholder) ───────────────────────────────────────────

@router.get("/tests", response_class=HTMLResponse)
async def tests(
    request: Request,
    user: User = Depends(require_admin),
):
    return templates.TemplateResponse("page_dashboard.html", {
        "request": request, "user": user, "active_page": "tests",
        "page_title": "Tests",
        "page_description": "Test UI components.",
    })


@router.get("/pricing", response_class=HTMLResponse)
async def pricing(
    request: Request,
    user: User = Depends(require_user),
):
    return templates.TemplateResponse("page_dashboard.html", {
        "request": request, "user": user, "active_page": "pricing",
        "page_title": "Pricing",
        "page_description": "Choose the plan that fits your needs.",
    })
