from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.database import engine, Base
from app.routers import auth, pages, dashboard, api, board, admin, settings as settings_router


# ── Lightweight SQLite migrations ────────────────────────────────────────────
# `Base.metadata.create_all` only creates *missing* tables — it never adds new
# columns to existing tables. For dev convenience we add any missing columns to
# pre-existing SQLite databases on startup.
NEW_USER_COLUMNS = [
    ("theme", "VARCHAR(16) DEFAULT 'system' NOT NULL"),
    ("accent", "VARCHAR(16) DEFAULT 'blue' NOT NULL"),
    ("density", "VARCHAR(16) DEFAULT 'comfortable' NOT NULL"),
    ("language", "VARCHAR(10) DEFAULT 'en' NOT NULL"),
    ("timezone", "VARCHAR(64) DEFAULT 'UTC' NOT NULL"),
    ("notify_product", "BOOLEAN DEFAULT 1 NOT NULL"),
    ("notify_security", "BOOLEAN DEFAULT 1 NOT NULL"),
    ("notify_marketing", "BOOLEAN DEFAULT 0 NOT NULL"),
    ("notify_weekly_digest", "BOOLEAN DEFAULT 1 NOT NULL"),
    ("account_name", "VARCHAR(100)"),
    ("bio", "TEXT"),
    ("is_admin", "BOOLEAN DEFAULT 0 NOT NULL"),
]


async def _migrate_sqlite(conn) -> None:
    res = await conn.execute(text("PRAGMA table_info(users)"))
    existing = {row[1] for row in res.fetchall()}
    if not existing:
        return  # table not created yet — create_all will do it
    # Rename legacy `workspace_name` → `account_name` if upgrading an old dev DB.
    if "workspace_name" in existing and "account_name" not in existing:
        await conn.execute(text("ALTER TABLE users RENAME COLUMN workspace_name TO account_name"))
        existing.discard("workspace_name")
        existing.add("account_name")
    for col, ddl in NEW_USER_COLUMNS:
        if col not in existing:
            await conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {ddl}"))

    # Drop legacy ActivityType rows (e.g. PAGE_VIEW) that no longer exist in
    # the trimmed enum, otherwise SQLAlchemy raises LookupError on read.
    try:
        await conn.execute(text(
            "DELETE FROM activities WHERE action NOT IN "
            "('LOGIN','SIGNUP','SETTINGS_CHANGE','API_CALL')"
        ))
    except Exception:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        try:
            await _migrate_sqlite(conn)
        except Exception:
            # Non-SQLite or already migrated — ignore.
            pass
    yield


app = FastAPI(title="Aceternity Dashboard", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

app.include_router(auth.router)
app.include_router(pages.router)
app.include_router(dashboard.router)
app.include_router(settings_router.router)
app.include_router(api.router)
app.include_router(board.router)
app.include_router(admin.router)
