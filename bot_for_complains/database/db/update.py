from sqlalchemy.ext.asyncio import AsyncSession

from database.models import BugData, BugReport

from .create import create_status

from .queries import (
    get_actual_status,
    get_actual_version,
)

from .common import (
    BugView,
    SEVERITY_NOT_SET,
    SEVERITY_VALUES,
    _bug_view_from_row,
)


async def update_bug(
    session: AsyncSession,
    bug_id: int,
    description: str,
    file_id: str,
    file_name: str,
) -> BugView | None:
    bug = await session.get(BugReport, bug_id)
    current_data = await get_actual_version(session, bug_id)
    last_status = await get_actual_status(session, bug_id)

    if bug is None or current_data is None:
        return None

    data = BugData(
        bug_id=bug_id,
        version=current_data.version + 1,
        description=description,
        report_file_id=file_id,
        report_file_name=file_name,
    )
    session.add(data)
    await session.flush()

    status = await create_status(
        session=session,
        bug_id=bug_id,
        bug_data_id=data.id,
        status="reopened",
        severity=last_status.severity if last_status else SEVERITY_NOT_SET,
    )

    await session.commit()
    return _bug_view_from_row(bug, data, status)

async def accept_bug(
    session: AsyncSession,
    bug_id: int,
    admin_id: int,
    admin_username: str | None,
) -> BugView | None:
    bug = await session.get(BugReport, bug_id)
    data = await get_actual_version(session, bug_id)

    if bug is None or data is None:
        return None

    status = await create_status(
        session=session,
        bug_id=bug_id,
        bug_data_id=data.id,
        status="in_progress",
        assigned_admin_id=admin_id,
        assigned_admin_username=admin_username,
    )

    await session.commit()
    return _bug_view_from_row(bug, data, status)

async def complete_bug_fix(
    session: AsyncSession,
    bug_id: int,
) -> BugView | None:
    bug = await session.get(BugReport, bug_id)
    data = await get_actual_version(session, bug_id)
    last_status = await get_actual_status(session, bug_id)

    if bug is None or data is None:
        return None

    status = await create_status(
        session=session,
        bug_id=bug_id,
        bug_data_id=data.id,
        status="waiting_confirmation",
        assigned_admin_id=last_status.assigned_admin_id
        if last_status
        else None,
        assigned_admin_username=last_status.assigned_admin_username
        if last_status
        else None,
    )

    await session.commit()
    return _bug_view_from_row(bug, data, status)

async def close_bug(
    session: AsyncSession,
    bug_id: int,
) -> BugView | None:
    bug = await session.get(BugReport, bug_id)
    data = await get_actual_version(session, bug_id)

    if bug is None or data is None:
        return None

    status = await create_status(
        session=session,
        bug_id=bug_id,
        bug_data_id=data.id,
        status="closed",
    )

    await session.commit()
    return _bug_view_from_row(bug, data, status)

async def reopen_bug(
    session: AsyncSession,
    bug_id: int,
) -> BugView | None:
    bug = await session.get(BugReport, bug_id)
    data = await get_actual_version(session, bug_id)

    if bug is None or data is None:
        return None

    status = await create_status(
        session=session,
        bug_id=bug_id,
        bug_data_id=data.id,
        status="reopened",
    )

    await session.commit()
    return _bug_view_from_row(bug, data, status)

async def set_bug_severity(
    session: AsyncSession,
    bug_id: int,
    severity: str,
) -> BugView | None:
    if severity not in SEVERITY_VALUES:
        raise ValueError(f"Unknown severity: {severity}")

    bug = await session.get(BugReport, bug_id)
    data = await get_actual_version(session, bug_id)
    last_status = await get_actual_status(session, bug_id)

    if bug is None or data is None or last_status is None:
        return None

    status = await create_status(
        session=session,
        bug_id=bug_id,
        bug_data_id=data.id,
        status=last_status.status,
        severity=severity,
        assigned_admin_id=last_status.assigned_admin_id,
        assigned_admin_username=last_status.assigned_admin_username,
    )

    await session.commit()
    return _bug_view_from_row(bug, data, status)

async def invalidate_bug(
    session: AsyncSession,
    bug_id: int,
) -> BugView | None:

    bug = await session.get(BugReport, bug_id)
    data = await get_actual_version(session, bug_id)

    if bug is None or data is None:
        return None

    status = await create_status(
        session=session,
        bug_id=bug_id,
        bug_data_id=data.id,
        status="invalid_description",
    )

    await session.commit()

    return _bug_view_from_row(
        bug,
        data,
        status,
    )

async def set_training_sample(
    session: AsyncSession,
    bug_data_id: int,
    value: bool,
) -> bool:

    bug_data = await session.get(
        BugData,
        bug_data_id,
    )

    if bug_data is None:
        return False

    if bug_data.is_training_sample == value:
        return False

    bug_data.is_training_sample = value

    await session.commit()

    return True