from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import BugData, BugReport, BugStatus

from .common import (
    BugView,
    _bug_view_from_row,
    _current_bug_stmt,
)

async def get_actual_version(
    session: AsyncSession,
    bug_id: int,
) -> BugData | None:
    result = await session.execute(
        select(BugData)
        .where(BugData.bug_id == bug_id)
        .order_by(BugData.version.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()

async def get_actual_status(
    session: AsyncSession,
    bug_id: int,
) -> BugStatus | None:
    result = await session.execute(
        select(BugStatus)
        .where(BugStatus.bug_id == bug_id)
        .order_by(BugStatus.created_at.desc(), BugStatus.id.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()

async def get_bug_by_id(
    session: AsyncSession,
    bug_id: int,
) -> BugView | None:
    result = await session.execute(
        _current_bug_stmt().where(BugReport.id == bug_id)
    )
    row = result.one_or_none()

    if row is None:
        return None

    return _bug_view_from_row(*row)

async def get_bug_version_by_number(
    session: AsyncSession,
    bug_id: int,
    version: int,
) -> BugView | None:
    bug = await session.get(BugReport, bug_id)

    result = await session.execute(
        select(BugData)
        .where(
            BugData.bug_id == bug_id,
            BugData.version == version,
        )
        .limit(1)
    )
    data = result.scalar_one_or_none()

    if bug is None or data is None:
        return None

    result = await session.execute(
        select(BugStatus)
        .where(BugStatus.bug_data_id == data.id)
        .order_by(BugStatus.created_at.desc(), BugStatus.id.desc())
        .limit(1)
    )
    status = result.scalar_one_or_none() or await get_actual_status(
        session,
        bug_id,
    )

    if status is None:
        return None

    return _bug_view_from_row(bug, data, status)

async def get_bug_history(
    session: AsyncSession,
    bug_id: int,
) -> list[BugData]:
    result = await session.execute(
        select(BugReport)
        .options(selectinload(BugReport.versions))
        .where(BugReport.id == bug_id)
    )
    bug = result.scalar_one_or_none()
    return bug.versions if bug else []

async def get_training_descriptions(
    session: AsyncSession,
) -> list[str]:
    result = await session.execute(
        select(BugData.description)
        .where(BugData.is_training_sample.is_(True))
    )

    return result.scalars().all()