from math import ceil

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import BugData, BugReport
from .common import _current_bug_stmt

async def get_bugs_count(session: AsyncSession) -> int:
    result = await session.execute(select(func.count(BugReport.id)))
    return result.scalar_one()

async def get_user_bugs_count(
    session: AsyncSession,
    user_id: int,
) -> int:
    result = await session.execute(
        select(func.count(BugReport.id)).where(BugReport.user_id == user_id)
    )
    return result.scalar_one()

async def get_bug_versions_count(
    session: AsyncSession,
    bug_id: int,
) -> int:
    result = await session.execute(
        select(func.count(BugData.id)).where(BugData.bug_id == bug_id)
    )
    return result.scalar_one()

async def get_admin_bugs_count(
    session: AsyncSession,
    admin_id: int,
) -> int:
    latest = _current_bug_stmt().subquery()

    result = await session.execute(
        select(func.count())
        .select_from(latest)
        .where(
            latest.c.assigned_admin_id == admin_id,
            latest.c.status == "in_progress",
        )
    )

    return result.scalar_one()

async def get_bug_page_count(
    session: AsyncSession,
    page_size: int,
) -> int:
    total = await get_bugs_count(session)

    if total == 0:
        return 0

    return ceil(total / page_size)

async def get_user_bug_page_count(
    session: AsyncSession,
    user_id: int,
    page_size: int,
) -> int:
    total = await get_user_bugs_count(
        session,
        user_id,
    )

    return ceil(total / page_size) if total else 0