from datetime import timedelta

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_user
from app.database import get_db
from app.models.account import Activity, Invoice, Subscription
from app.models.user import User
from app.services.plans import PLANS, PLAN_SLUGS, get_plan, plan_price

router = APIRouter(prefix="/dashboard")
templates = Jinja2Templates(directory="app/templates")


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

    return templates.TemplateResponse("dashboard.html", {
        "request": request, "user": user, "activities": activities,
        "active_page": "overview",
    })


# ── Subscription ────────────────────────────────────────────────────────────

async def _get_or_create_subscription(db: AsyncSession, user: User) -> Subscription:
    res = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
    sub = res.scalar_one_or_none()
    if sub is None:
        sub = Subscription(user_id=user.id, plan=user.subscription_tier or "free")
        db.add(sub)
        await db.flush()
    return sub


def _next_invoice_number(prefix: str = "INV") -> str:
    # Time-based, no DB roundtrip required; uniqueness enforced by UNIQUE column.
    from datetime import datetime, timezone
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"


@router.get("/subscriptions", response_class=HTMLResponse)
async def subscriptions_page(
    request: Request,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_or_create_subscription(db, user)
    inv_res = await db.execute(
        select(Invoice).where(Invoice.user_id == user.id)
        .order_by(Invoice.issued_at.desc()).limit(20)
    )
    invoices = inv_res.scalars().all()

    return templates.TemplateResponse("subscriptions.html", {
        "request": request,
        "user": user,
        "subscription": sub,
        "current_plan": get_plan(sub.plan),
        "plans": PLANS,
        "invoices": invoices,
        "active_page": "subscriptions",
    })


@router.post("/subscriptions/change")
async def subscriptions_change(
    plan: str = Form(...),
    interval: str = Form("monthly"),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    if plan not in PLAN_SLUGS:
        return JSONResponse({"ok": False, "error": "Unknown plan."}, status_code=400)
    if interval not in {"monthly", "yearly"}:
        return JSONResponse({"ok": False, "error": "Unknown interval."}, status_code=400)

    sub = await _get_or_create_subscription(db, user)
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    sub.plan = plan
    sub.interval = interval
    sub.status = "active"
    sub.cancel_at_period_end = False
    sub.current_period_start = now
    sub.current_period_end = now + (timedelta(days=365) if interval == "yearly" else timedelta(days=30))

    user.subscription_tier = plan

    # Mock-charge: write a paid invoice for any non-free plan.
    p = get_plan(plan)
    if p and not p.is_free:
        amount = plan_price(plan, interval) * 100  # cents
        db.add(Invoice(
            user_id=user.id,
            number=_next_invoice_number(),
            plan=plan,
            interval=interval,
            amount_cents=amount,
            currency="usd",
            status="paid",
            issued_at=now,
        ))

    await db.flush()
    return JSONResponse({"ok": True, "plan": plan, "interval": interval})


@router.post("/subscriptions/cancel")
async def subscriptions_cancel(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_or_create_subscription(db, user)
    sub.cancel_at_period_end = True
    sub.status = "cancelled"
    await db.flush()
    return JSONResponse({"ok": True})
