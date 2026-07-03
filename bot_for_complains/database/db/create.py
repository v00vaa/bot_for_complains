import logging
from venv import logger

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import BugData, BugReport, BugStatus
from services.bug_analyzer import generate_bug_title

from .common import (
    BugView,
    SEVERITY_NOT_SET,
    _bug_view_from_row,
)

from .queries import (
    get_actual_status,
)

logger = logging.getLogger(__name__)

async def create_bug(
    session: AsyncSession,
    user_id: int,
    description: str,
    file_id: str,
    file_name: str,
) -> BugView:
    bug = BugReport(
        user_id=user_id,
        title=generate_bug_title(description),
    )
    session.add(bug)
    await session.flush()

    data = BugData(
        bug_id=bug.id,
        version=1,
        description=description,
        report_file_id=file_id,
        report_file_name=file_name,
    )
    session.add(data)
    await session.flush()

    status = await create_status(
        session=session,
        bug_id=bug.id,
        bug_data_id=data.id,
        status="new",
        severity=SEVERITY_NOT_SET,
    )

    await session.commit()
    return _bug_view_from_row(bug, data, status)

async def create_status(
    session: AsyncSession,
    bug_id: int,
    bug_data_id: int,
    status: str,
    severity: str | None = None,
    assigned_admin_id: int | None = None,
    assigned_admin_username: str | None = None,
) -> BugStatus:
    last_status = await get_actual_status(session, bug_id)

    status_row = BugStatus(
        bug_id=bug_id,
        bug_data_id=bug_data_id,
        status=status,
        severity=severity
        or (last_status.severity if last_status else SEVERITY_NOT_SET),
        assigned_admin_id=assigned_admin_id,
        assigned_admin_username=assigned_admin_username,
    )
    session.add(status_row)
    await session.flush()

    logger.info(
        "Created status '%s' for bug #%s, data #%s",
        status,
        bug_id,
        bug_data_id,
    )
    return status_row


