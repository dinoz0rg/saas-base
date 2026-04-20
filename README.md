# Tracker — Linear-style Project Management SaaS

A clean, minimal project management board inspired by [Linear](https://linear.app) / Aceternity, built with Python.

## Stack

- **Backend:** FastAPI + SQLAlchemy 2.0 (async)
- **Frontend:** Jinja2 templates + Tailwind CSS (CDN)
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **IDs:** UUIDv7 (time-sortable)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Seed demo data
python -m app.seed

# Run the app
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## Project Structure

```
app/
├── main.py              # FastAPI entry point
├── config.py            # Settings via pydantic-settings
├── database.py          # Async SQLAlchemy engine & session
├── seed.py              # Demo data seeder
├── models/
│   └── issue.py         # Workspace, Project, Issue, Label models
├── schemas/
│   └── issue.py         # Pydantic request/response schemas
├── services/
│   └── issue.py         # Business logic & queries
├── routers/
│   ├── board.py         # HTML board views
│   └── api.py           # REST API endpoints
└── templates/
    ├── base.html         # Layout with Tailwind
    ├── board.html        # Kanban board page
    ├── empty.html        # Empty state
    ├── redirect.html     # Auto-redirect
    └── components/
        ├── sidebar.html      # Navigation sidebar
        └── issue_card.html   # Issue card component
```

## Configuration

Copy `.env.example` to `.env` and adjust:

```env
DATABASE_URL=sqlite+aiosqlite:///./data/app.db
# For production:
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/saas_db
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Redirect to default board |
| `GET` | `/{workspace}/{project}/board` | Kanban board view |
| `POST` | `/api/projects/{id}/issues` | Create issue |
| `PATCH` | `/api/issues/{id}` | Update issue |
| `PATCH` | `/api/issues/{id}/status` | Change issue status |
