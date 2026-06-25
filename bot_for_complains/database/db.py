import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models import BugReport, BugStatus, BugVersion

from services import generate_bug_title, determine_severity


logger = logging.getLogger(__name__)


from sqlalchemy import case

SEVERITY_ORDER = case(
    (BugReport.severity == "not_set", 0),
    (BugReport.severity == "critical", 1),
    (BugReport.severity == "high", 2),
    (BugReport.severity == "medium", 3),
    (BugReport.severity == "low", 4),
    else_=5,
)

async def create_bug(
    session: AsyncSession,
    user_id: int,
    description: str,
    file_id: str,
    file_name: str,
):
    bug = BugReport(
        user_id=user_id,
        title=generate_bug_title(description),
        severity=determine_severity(description),
    )

    session.add(bug)
    await session.flush()

    version = BugVersion(
        bug_id=bug.id,
        version=1,
        description=description,
        report_file_id=file_id,
        report_file_name=file_name,
    )

    session.add(version)
    await session.flush()

    status = BugStatus(
        bug_version_id=version.id,
        status="new",
    )

    session.add(status)

    await session.commit()

    return bug

async def get_actual_version(
    session: AsyncSession,
    bug_id: int,
):
    result = await session.execute(
        select(BugVersion)
        .where(BugVersion.bug_id == bug_id)
        .order_by(BugVersion.version.desc())
        .limit(1)
    )

    return result.scalar_one_or_none()

async def get_actual_status(
    session: AsyncSession,
    version_id: int,
):
    result = await session.execute(
        select(BugStatus)
        .where(
            BugStatus.bug_version_id == version_id
        )
        .order_by(
            BugStatus.created_at.desc()
        )
        .limit(1)
    )

    return result.scalar_one_or_none()

async def update_bug(
    session: AsyncSession,
    bug_id: int,
    description: str,
    file_id: str,
    file_name: str,
):
    current_version = await get_actual_version(
        session,
        bug_id,
    )

    if current_version is None:
        return None

    version = BugVersion(
        bug_id=bug_id,
        version=current_version.version + 1,
        description=description,
        report_file_id=file_id,
        report_file_name=file_name,
    )

    session.add(version)
    await session.flush()

    status = BugStatus(
        bug_version_id=version.id,
        status="new",
    )

    session.add(status)

    await session.commit()

    return version

async def get_bug_by_id(
    session: AsyncSession,
    bug_id: int,
):
    result = await session.execute(
        select(BugReport)
        .where(BugReport.id == bug_id)
    )

    return result.scalar_one_or_none()

async def accept_bug(
    session: AsyncSession,
    bug_id: int,
    admin_id: int,
    admin_username: str,
):
    version = await get_actual_version(
        session,
        bug_id,
    )

    if version is None:
        return None

    status = BugStatus(
        bug_version_id=version.id,
        status="in_progress",
        assigned_admin_id=admin_id,
        assigned_admin_username=admin_username,
    )

    session.add(status)

    await session.commit()

    return version

async def complete_bug_fix(
    session: AsyncSession,
    bug_id: int,
):
    version = await get_actual_version(
        session,
        bug_id,
    )

    if version is None:
        return None

    last_status = await get_actual_status(
        session,
        version.id,
    )

    status = BugStatus(
        bug_version_id=version.id,
        status="waiting_confirmation",
        assigned_admin_id=last_status.assigned_admin_id,
        assigned_admin_username=last_status.assigned_admin_username,
    )

    session.add(status)

    await session.commit()

    return version

async def close_bug(
    session: AsyncSession,
    bug_id: int,
):
    version = await get_actual_version(
        session,
        bug_id,
    )

    if version is None:
        return None

    status = BugStatus(
        bug_version_id=version.id,
        status="closed",
    )

    session.add(status)

    await session.commit()

    return version

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from .models import (
    BugReport,
    BugStatus,
    BugData,
)


async def get_bugs_list(
    session: AsyncSession,
) -> list[tuple[BugReport, BugStatus]]:
    latest_status = (
        select(
            BugStatus.bug_id,
            func.max(BugStatus.id).label("status_id"),
        )
        .group_by(BugStatus.bug_id)
        .subquery()
    )

    stmt = (
        select(
            BugReport,
            BugStatus,
        )
        .join(
            latest_status,
            latest_status.c.bug_id == BugReport.id,
        )
        .join(
            BugStatus,
            BugStatus.id == latest_status.c.status_id,
        )
        .order_by(
            SEVERITY_ORDER,
            BugReport.id.desc(),
        )
    )

    result = await session.execute(stmt)

    return result.all()

async def get_admin_bugs(
    session: AsyncSession,
    admin_id: int,
) -> list[tuple[BugReport, BugStatus]]:
    latest_status = (
        select(
            BugStatus.bug_id,
            func.max(BugStatus.id).label("status_id"),
        )
        .group_by(BugStatus.bug_id)
        .subquery()
    )

    stmt = (
        select(
            BugReport,
            BugStatus,
        )
        .join(
            latest_status,
            latest_status.c.bug_id == BugReport.id,
        )
        .join(
            BugStatus,
            BugStatus.id == latest_status.c.status_id,
        )
        .where(
            BugStatus.assigned_admin_id == admin_id,
            BugStatus.status == "in_progress",
        )
        .order_by(
            SEVERITY_ORDER,
            BugReport.id.desc(),
        )
    )

    result = await session.execute(stmt)

    return result.all()

