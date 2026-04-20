"""Seed the database with demo data matching the Linear-style screenshot."""
import asyncio

from sqlalchemy import select

from app.database import async_session, engine, Base
from app.models.issue import (
    Issue, IssueStatus, IssuePriority, Label, Project, Workspace,
)


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # Check if already seeded
        existing = await db.execute(select(Workspace).limit(1))
        if existing.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        # Workspace
        ws = Workspace(name="Aceternity", slug="aceternity")
        db.add(ws)
        await db.flush()

        # Project
        proj = Project(name="Aceternity Core", prefix="ACE", workspace_id=ws.id)
        db.add(proj)
        await db.flush()

        # Labels
        labels = {}
        label_data = [
            ("Document", "red"),
            ("Wisdom", "green"),
            ("Task", "gray"),
            ("UI", "blue"),
            ("Task - Content", "orange"),
            ("Improvement", "blue"),
            ("Long term", "orange"),
        ]
        for name, color in label_data:
            label = Label(name=name, color=color, project_id=proj.id)
            db.add(label)
            await db.flush()
            labels[name] = label

        # Issues — Backlog
        backlog_issues = [
            (179, "Acebuilder V2", IssuePriority.NONE, "Manu", ["Document"]),
            (148, "Easiest way to get clients (READ DESCRIPTION)", IssuePriority.URGENT, "Manu", ["Wisdom"]),
            (213, "Change pricing for aceternity ui -- free / pro / custom. Keep bigger pricings on...", IssuePriority.URGENT, "Manu", []),
            (208, "Aceternity UI Component", IssuePriority.URGENT, None, ["Task", "UI"]),
            (120, "Reels recording", IssuePriority.MEDIUM, None, ["Task - Content"]),
            (232, "Revamp algochurn", IssuePriority.NONE, None, []),
            (166, "Screenshots from local", IssuePriority.NONE, None, ["Wisdom"]),
            (116, "AI SaaS Template V2", IssuePriority.NONE, None, ["Task"]),
            (185, "Real estate template for Aceternity UI Pro", IssuePriority.NONE, None, []),
        ]
        for num, title, priority, assignee, issue_labels in backlog_issues:
            issue = Issue(
                number=num, title=title, status=IssueStatus.BACKLOG,
                priority=priority, project_id=proj.id, assignee_name=assignee,
            )
            issue.labels = [labels[l] for l in issue_labels]
            db.add(issue)

        # Issues — Todo
        todo_issues = [
            (228, "Optimize for chatgpt", IssuePriority.URGENT, "Manu", ["Improvement"]),
            (199, "Youtube Recording", IssuePriority.URGENT, None, ["Task - Content"]),
            (235, "Start Suri Electricals", IssuePriority.NONE, "Manu", []),
            (225, "CLIENTS: Private Equity Firms, Law Firms, Venture Capitalists, Real Estate.", IssuePriority.NONE, "Manu", ["Long term", "Wisdom"]),
        ]
        for num, title, priority, assignee, issue_labels in todo_issues:
            issue = Issue(
                number=num, title=title, status=IssueStatus.TODO,
                priority=priority, project_id=proj.id, assignee_name=assignee,
            )
            issue.labels = [labels[l] for l in issue_labels]
            db.add(issue)

        # Issues — In Progress
        in_progress_issues = [
            (243, "List of component blocks for Aceternity UI Pro", IssuePriority.HIGH, "Manu", []),
            (250, "Add 4 new components everyday to Pro Aceternity.", IssuePriority.HIGH, "Manu", []),
            (249, "Acebuilder launch checklist", IssuePriority.HIGH, "Manu", []),
            (245, "Add description to all the components in Aceternity Pro", IssuePriority.HIGH, "Manu", []),
            (244, "Add purchase stripe links directly on the website", IssuePriority.HIGH, "Manu", []),
        ]
        for num, title, priority, assignee, issue_labels in in_progress_issues:
            issue = Issue(
                number=num, title=title, status=IssueStatus.IN_PROGRESS,
                priority=priority, project_id=proj.id, assignee_name=assignee,
            )
            issue.labels = [labels[l] for l in issue_labels]
            db.add(issue)

        # Issues — Done (bulk)
        for i in range(133):
            issue = Issue(
                number=i + 1, title=f"Completed task #{i + 1}",
                status=IssueStatus.DONE, priority=IssuePriority.NONE,
                project_id=proj.id, assignee_name="Manu",
            )
            db.add(issue)

        # Issues — Cancelled
        for i in range(8):
            issue = Issue(
                number=300 + i, title=f"Cancelled task #{i + 1}",
                status=IssueStatus.CANCELLED, priority=IssuePriority.NONE,
                project_id=proj.id,
            )
            db.add(issue)

        await db.commit()
        print("Seed data created successfully!")
        print(f"  Workspace: {ws.name} (/{ws.slug})")
        print(f"  Project: {proj.name} ({proj.prefix})")
        print(f"  Board URL: /{ws.slug}/{proj.prefix}/board")


if __name__ == "__main__":
    asyncio.run(seed())
