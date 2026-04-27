# SaaS Base — Aceternity

A clean, reusable **SaaS starter** built with FastAPI + Jinja2 + Tailwind, styled
after Linear / Aceternity. Use this repo as the foundation for new SaaS
projects (e.g. social-media post automators, like/comment boosters, content
schedulers, lead-gen tools, …) — fork it, drop in your domain feature, ship.

This is **not** a multi-tenant workspace product. It's a single-account-per-user
base with the boring pieces already wired up: auth, account settings, API keys,
billing tier UI, an activity/metrics model, and a polished sidebar/dashboard
shell.

## What's Included

- **Auth** — email/password login, registration, optional 2FA (TOTP), session list.
- **Account settings** — profile, appearance (theme/accent/density), language,
  timezone, notifications, sessions, API keys, billing tier UI, danger zone.
- **Generic SaaS models** — `Activity`, `Metric`, `Page`, `ApiKey` per user
  (in `app/models/account.py`). Re-use or replace with your feature's models.
- **Dashboard shell** — sidebar, top bar, "Ask Navigator" command palette,
  pages list, reports view (sparkline + activity breakdown).
- **Lightweight migrations** — startup-time `ALTER TABLE` for SQLite dev DBs in
  `app/main.py`, so schema tweaks during early development don't require Alembic.

## Stack

- **Backend:** FastAPI + SQLAlchemy 2.0 (async)
- **Frontend:** Jinja2 templates + Tailwind CSS (CDN)
- **Database:** SQLite (dev) / PostgreSQL (prod) via `asyncpg`
- **IDs:** UUIDv7 (time-sortable)

## Quick Start

```bash
pip install -r requirements.txt

# Seed demo data (creates admin user, sample pages, activities, metrics)
python -m app.seed

# Run
python run.py        # listens on 0.0.0.0:5000
# or: uvicorn app.main:app --reload --port 5000
```

Open <http://localhost:5000> in your browser.

## Project Structure

```
app/
├── main.py              # FastAPI entry point + lightweight SQLite migrations
├── config.py            # Settings via pydantic-settings
├── database.py          # Async SQLAlchemy engine & session
├── auth.py              # Password hashing, cookie auth, dependencies
├── seed.py              # Demo data seeder
├── models/
│   ├── user.py          # User, UserSession
│   ├── account.py       # Activity, Metric, Page, ApiKey  (generic SaaS entities)
│   ├── issue.py         # Sample feature: Issue / status / priority
│   └── chat.py          # Ask-Navigator chat sessions
├── schemas/             # Pydantic request/response schemas
├── services/            # Business logic & queries
├── routers/
│   ├── auth.py          # /login, /register, /logout, 2FA
│   ├── dashboard.py     # /dashboard (overview, pages, reports, page editor)
│   ├── settings.py      # /dashboard/settings (tabbed)
│   ├── board.py         # Sample feature: Kanban board (admin-only)
│   ├── pages.py         # Public marketing pages (landing, pricing)
│   └── api.py           # JSON API endpoints
├── static/              # css/, js/ (app.js, navigator.js, …), uploads/
└── templates/
    ├── base.html
    ├── landing.html, pricing.html
    ├── dashboard.html, pages.html, reports.html, settings.html, board.html
    ├── auth/            # login, register, 2FA
    ├── components/      # sidebar.html, issue_card.html
    └── settings/        # _general, _appearance, _notifications, _security,
                         #  _sessions, _api_keys, _billing, _danger
```

## Configuration

Copy `.env.example` to `.env` and adjust:

```env
DATABASE_URL=sqlite+aiosqlite:///./data/app.db
# For production:
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/saas_db
```

## Using This as a Base for a New SaaS

1. **Clone & rename** the repo / `app/` package as you like.
2. **Add your domain models** alongside `account.py` (e.g. `models/post.py`,
   `models/campaign.py`). Register them in `app/models/__init__.py` so
   `Base.metadata.create_all` picks them up.
3. **Add a router** under `app/routers/` and include it in `app/main.py`.
4. **Plug into the sidebar** — edit `app/templates/components/sidebar.html` to
   surface your new feature next to the existing nav items.
5. **Replace `Issue` / `Page`** sample features if you don't need them, or keep
   them as reference.
6. **Update branding** — the hardcoded "Aceternity" label in
   `templates/components/sidebar.html` is the main visible brand string.

## Conventions

- **IDs** — `String(36)` UUIDv7 primary keys via `uuid_utils.uuid7`.
- **Timestamps** — timezone-aware UTC (`datetime.now(timezone.utc)`).
- **Forms** — JSON endpoints under `/dashboard/settings/*` consumed by
  `static/js/settings.js`; HTML pages render via Jinja2 with a shared
  `base.html` layout.
- **Migrations** — for dev convenience, list new `users` columns in
  `NEW_USER_COLUMNS` in `app/main.py`. For production, switch to Alembic.
