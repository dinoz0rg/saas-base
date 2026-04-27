# SaaS Base — Aceternity

A clean, reusable **SaaS starter** built with FastAPI + Jinja2 + Tailwind, styled
after Linear / Aceternity. Use this repo as the foundation for new SaaS
projects (e.g. social-media post automators, like/comment boosters, content
schedulers, lead-gen tools, …) — fork it, drop in your domain feature, ship.

This is **not** a multi-tenant workspace product. It's a single-account-per-user
base with the boring pieces already wired up: auth, account settings, API keys,
sessions, an activity feed, and a polished sidebar/dashboard shell with a
real OpenAI-powered "Ask Navigator" assistant.

## What's Included

- **Auth** — email/password login, registration, optional 2FA (TOTP), active
  session list with per-device revoke.
- **Account settings** — profile, appearance (theme/accent/density), language,
  timezone, notifications, sessions, API keys, billing tier UI, danger zone.
- **Activity feed** — generic `Activity` model + dashboard "Recent Activity"
  card. Wire your own events into it.
- **API keys** — issue + revoke programmatic credentials per user.
- **Ask Navigator** — sidebar AI assistant powered by OpenAI Chat Completions
  (`/api/ai/ask`), with persisted chat history and ChatGPT-style auto-titles.
- **Quick Search** — `/`-key fast client-side search across sidebar destinations.
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

# Seed demo data (creates admin user + a few activity rows)
python -m app.seed

# Run
python run.py        # listens on 0.0.0.0:5000
# or: uvicorn app.main:app --reload --port 5000
```

Open <http://localhost:5000>. Demo login: `demo@aceternity.dev` / `demo1234`.

## Project Structure

```
app/
├── main.py              # FastAPI entry point + lightweight SQLite migrations
├── config.py            # Settings via pydantic-settings (incl. OPENAI_API_KEY)
├── database.py          # Async SQLAlchemy engine & session
├── auth.py              # Password hashing, cookie auth, dependencies
├── seed.py              # Demo data seeder
├── models/
│   ├── user.py          # User, UserSession
│   ├── account.py       # Activity, ApiKey  (generic SaaS entities)
│   └── chat.py          # Ask-Navigator chat sessions
├── routers/
│   ├── auth.py          # /login, /register, /logout, 2FA
│   ├── dashboard.py     # /dashboard overview
│   ├── settings.py      # /dashboard/settings (tabbed)
│   ├── pages.py         # Landing + profile redirects + sessions API
│   └── api.py           # /api/chats (chat history) + /api/ai/ask (OpenAI)
├── static/              # css/, js/ (app.js, navigator.js, search.js, …), uploads/
└── templates/
    ├── base.html, landing.html, dashboard.html, settings.html, redirect.html
    ├── auth/            # login, register, 2FA
    ├── components/      # sidebar.html (incl. Ask Navigator + Search modals)
    └── settings/        # _general, _appearance, _notifications, _security,
                         #  _sessions, _api_keys, _billing, _danger
```

## Configuration

Copy `.env.example` to `.env` (or create `.env`) and set at minimum:

```env
DATABASE_URL=sqlite+aiosqlite:///./data/app.db
SECRET_KEY=change-me
OPENAI_API_KEY=sk-...        # required for Ask Navigator
OPENAI_MODEL=gpt-4o-mini

# For production:
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/saas_db
```

## Using This as a Base for a New SaaS

1. **Clone & rename** the repo / `app/` package as you like.
2. **Add your domain models** alongside `account.py` (e.g. `models/post.py`,
   `models/campaign.py`). Register them in `app/models/__init__.py` so
   `Base.metadata.create_all` picks them up.
3. **Add a router** under `app/routers/` (mirror `dashboard.py`) and include it
   in `app/main.py`.
4. **Plug into the sidebar** — edit `app/templates/components/sidebar.html` to
   surface your new feature alongside Home / Settings.
5. **Update branding** — the hardcoded "Aceternity" label in
   `templates/components/sidebar.html` and `landing.html` is the main visible
   brand string.

## Conventions

- **IDs** — `String(36)` UUIDv7 primary keys via `uuid_utils.uuid7`.
- **Timestamps** — timezone-aware UTC (`datetime.now(timezone.utc)`).
- **Forms** — JSON endpoints under `/dashboard/settings/*` consumed by
  `static/js/settings.js`; HTML pages render via Jinja2 with a shared
  `base.html` layout.
- **Migrations** — for dev convenience, list new `users` columns in
  `NEW_USER_COLUMNS` in `app/main.py`. For production, switch to Alembic.
