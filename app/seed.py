"""Seed the database with a demo admin user and a few activity rows.

This is intentionally minimal — the project is a SaaS *base*. Add seed data
for your specific vertical (post automator, social booster, etc.) when you
fork this repo for a new product.
"""
import asyncio
from datetime import datetime, timezone, timedelta

from sqlalchemy import select

from app.database import async_session, engine, Base
from app.auth import hash_password
from app.models.user import User
from app.models.account import Activity, ActivityType, Subscription, Invoice


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        existing = await db.execute(select(User).limit(1))
        if existing.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        now = datetime.now(timezone.utc)

        # Demo user (admin)
        user = User(
            email="demo@aceternity.dev",
            display_name="Manu Arora",
            hashed_password=hash_password("demo1234"),
            is_admin=True,
            subscription_tier="pro",
        )
        db.add(user)
        await db.flush()

        # Active Pro subscription with one paid invoice for a richer demo.
        db.add(Subscription(
            user_id=user.id,
            plan="pro",
            interval="monthly",
            status="active",
            current_period_start=now - timedelta(days=12),
            current_period_end=now + timedelta(days=18),
        ))
        db.add(Invoice(
            user_id=user.id,
            number=f"INV-{now.strftime('%Y%m%d')}-0001",
            plan="pro",
            interval="monthly",
            amount_cents=1900,
            currency="usd",
            status="paid",
            issued_at=now - timedelta(days=12),
        ))

        # A few generic activity rows so the dashboard isn't empty on first run.
        activities_data = [
            (ActivityType.SIGNUP, "Account created", 48),
            (ActivityType.LOGIN, "Logged in from Chrome on macOS", 10),
            (ActivityType.SETTINGS_CHANGE, "Updated notification preferences", 30),
            (ActivityType.API_CALL, "Generated new API key", 4),
        ]
        for action, description, hours_ago in activities_data:
            db.add(Activity(
                user_id=user.id,
                user_name=user.display_name,
                action=action,
                description=description,
                created_at=now - timedelta(hours=hours_ago),
            ))

        await db.commit()
        print("Seed data created successfully!")
        print(f"  User: {user.email} / demo1234 (admin)")
        print(f"  Dashboard: /dashboard")


if __name__ == "__main__":
    asyncio.run(seed())
