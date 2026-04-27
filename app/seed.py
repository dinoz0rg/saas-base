"""Seed the database with demo data for the dashboard SaaS."""
import asyncio
from datetime import datetime, timezone, timedelta

from sqlalchemy import select

from app.database import async_session, engine, Base
from app.auth import hash_password
from app.models.user import User
from app.models.account import Activity, ActivityType, Metric, MetricPeriod, Page
from app.models.issue import Issue, IssueStatus, IssuePriority


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
        )
        db.add(user)
        await db.flush()

        # Pages
        pages_data = [
            ("Getting Started", "getting-started", "Welcome to Aceternity! This guide will help you set up your dashboard.", True, 1247),
            ("API Documentation", "api-docs", "Complete reference for the Aceternity API endpoints and authentication.", True, 892),
            ("Changelog", "changelog", "All notable changes to the Aceternity platform.", True, 634),
            ("Component Library", "components", "Browse and preview all available UI components.", True, 2103),
            ("Pricing Plans", "pricing", "Compare features across Free, Pro, and Enterprise plans.", True, 1856),
            ("Blog: Building Modern UIs", "blog-modern-uis", "How we approach building clean, minimal interfaces.", True, 423),
            ("Templates Gallery", "templates", "Pre-built templates for common SaaS patterns.", True, 967),
            ("Integration Guide", "integrations", "Connect Aceternity with your existing tools and workflows.", True, 312),
            ("Roadmap", "roadmap", "What we're building next — public product roadmap.", False, 156),
            ("Design System", "design-system", "Typography, colors, spacing, and component guidelines.", False, 89),
            ("Team Handbook", "handbook", "Internal processes and team guidelines.", False, 45),
            ("Migration Guide v2", "migration-v2", "Steps to migrate from v1 to v2 of the platform.", False, 23),
        ]
        for i, (title, slug, content, published, views) in enumerate(pages_data):
            page = Page(
                user_id=user.id,
                title=title,
                slug=slug,
                content=content,
                is_published=published,
                views_count=views,
                created_at=now - timedelta(days=30 - i),
                updated_at=now - timedelta(days=max(0, 10 - i)),
            )
            db.add(page)

        # Activities
        activities_data = [
            ("Manu Arora", ActivityType.PAGE_VIEW, "Viewed Component Library page", 0.5),
            ("Manu Arora", ActivityType.SETTINGS_CHANGE, "Updated billing settings", 1),
            ("Manu Arora", ActivityType.EXPORT, "Exported analytics report for March 2026", 2),
            ("Manu Arora", ActivityType.PAGE_VIEW, "Viewed API Documentation", 3),
            ("Manu Arora", ActivityType.API_CALL, "Generated new API key", 4),
            ("Manu Arora", ActivityType.UPLOAD, "Uploaded hero-banner.png to assets", 5),
            ("Manu Arora", ActivityType.PAGE_VIEW, "Viewed Pricing Plans page", 6),
            ("Manu Arora", ActivityType.SETTINGS_CHANGE, "Enabled custom domain feature", 8),
            ("Manu Arora", ActivityType.LOGIN, "Logged in from Chrome on macOS", 10),
            ("Manu Arora", ActivityType.PAGE_VIEW, "Viewed Getting Started guide", 12),
            ("Manu Arora", ActivityType.EXPORT, "Exported page analytics as CSV", 16),
            ("Manu Arora", ActivityType.API_CALL, "Called /api/v1/pages endpoint", 18),
            ("Manu Arora", ActivityType.PAGE_VIEW, "Viewed Templates Gallery", 20),
            ("Manu Arora", ActivityType.LOGIN, "Logged in from Safari on iPhone", 24),
            ("Manu Arora", ActivityType.SETTINGS_CHANGE, "Updated notification preferences", 30),
            ("Manu Arora", ActivityType.PAGE_VIEW, "Viewed Changelog", 36),
            ("Manu Arora", ActivityType.SIGNUP, "Account created", 48),
        ]
        for user_name, action, description, hours_ago in activities_data:
            activity = Activity(
                user_id=user.id,
                user_name=user_name,
                action=action,
                description=description,
                created_at=now - timedelta(hours=hours_ago),
            )
            db.add(activity)

        # Metrics
        metric_names = ["page_views", "api_calls", "active_users", "bandwidth_mb"]
        for day_offset in range(30):
            day = now - timedelta(days=day_offset)
            for name in metric_names:
                base_values = {"page_views": 150, "api_calls": 80, "active_users": 12, "bandwidth_mb": 45}
                import random
                random.seed(day_offset * 100 + hash(name))
                value = base_values[name] * (0.7 + random.random() * 0.6)
                metric = Metric(
                    user_id=user.id,
                    name=name,
                    value=round(value, 1),
                    period=MetricPeriod.DAILY,
                    recorded_at=day,
                )
                db.add(metric)

        # Planning issues for admin kanban board
        issues_data = [
            ("Add Stripe subscription integration", "Integrate Stripe for payment processing and subscription management.", IssueStatus.todo, IssuePriority.urgent, "Feature", "Manu"),
            ("Design onboarding flow for new users", "Create step-by-step onboarding with tooltips and guided tour.", IssueStatus.todo, IssuePriority.high, "Design", "Manu"),
            ("Set up CI/CD pipeline", "Configure GitHub Actions for automated testing and deployment.", IssueStatus.in_progress, IssuePriority.high, "DevOps", "Manu"),
            ("Implement dark mode toggle", "Add dark/light theme switch with system preference detection.", IssueStatus.backlog, IssuePriority.medium, "Feature", None),
            ("Write API documentation", "Document all REST API endpoints with examples.", IssueStatus.in_progress, IssuePriority.medium, "Docs", "Manu"),
            ("Add email notification system", "Transactional emails for account events and weekly digests.", IssueStatus.backlog, IssuePriority.medium, "Feature", None),
            ("Fix mobile responsive layout issues", "Sidebar and dashboard cards break on small screens.", IssueStatus.todo, IssuePriority.high, "Bug", "Manu"),
            ("Add user avatar upload", "Allow users to upload profile photos with image cropping.", IssueStatus.backlog, IssuePriority.low, "Feature", None),
            ("Implement rate limiting on API", "Prevent abuse with per-user rate limits on API endpoints.", IssueStatus.backlog, IssuePriority.medium, "Security", None),
            ("Create admin user management page", "List, search, edit, and deactivate user accounts.", IssueStatus.todo, IssuePriority.high, "Feature", "Manu"),
            ("Add analytics export to CSV", "Let users download their analytics data as CSV files.", IssueStatus.backlog, IssuePriority.low, "Feature", None),
            ("Set up error monitoring with Sentry", "Integrate Sentry for real-time error tracking in production.", IssueStatus.done, IssuePriority.high, "DevOps", "Manu"),
            ("Add two-factor authentication", "TOTP-based 2FA for enhanced account security.", IssueStatus.backlog, IssuePriority.medium, "Security", None),
            ("Refactor database queries for performance", "Optimize slow queries identified in production logs.", IssueStatus.in_progress, IssuePriority.medium, "Performance", "Manu"),
            ("Create landing page A/B test", "Test two hero variants to optimize conversion rate.", IssueStatus.done, IssuePriority.medium, "Marketing", "Manu"),
            ("Add webhook support for integrations", "Allow users to receive event webhooks at custom URLs.", IssueStatus.backlog, IssuePriority.low, "Feature", None),
            ("Fix login session timeout bug", "Users are logged out after 30 min despite remember-me.", IssueStatus.done, IssuePriority.urgent, "Bug", "Manu"),
            ("Implement search across all pages", "Full-text search with instant results dropdown.", IssueStatus.backlog, IssuePriority.medium, "Feature", None),
            ("Write terms of service and privacy policy", "Legal pages required before public launch.", IssueStatus.cancelled, IssuePriority.low, "Legal", None),
            ("Add keyboard shortcuts help modal", "Show available shortcuts when pressing ? key.", IssueStatus.backlog, IssuePriority.none, "Feature", None),
        ]
        for i, (title, desc, status, priority, label, assignee) in enumerate(issues_data):
            issue = Issue(
                identifier=f"ACE-{i + 1}",
                title=title,
                description=desc,
                status=status,
                priority=priority,
                label=label,
                assignee=assignee,
                sort_order=i,
                created_by=user.id,
                created_at=now - timedelta(days=20 - i),
            )
            db.add(issue)

        await db.commit()
        print("Seed data created successfully!")
        print(f"  User: {user.email} / demo1234 (admin)")
        print(f"  Dashboard: /dashboard")
        print(f"  Board: /dashboard/board (admin only)")


if __name__ == "__main__":
    asyncio.run(seed())
