import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models import BugReport

from services import generate_bug_title, determine_severity


logger = logging.getLogger(__name__)


async def create_bug(
    session,
    user_id: int,
    description: str,
    file_id: str,
    file_name: str,
) -> BugReport:

    bug = BugReport(
        user_id=user_id,
        title=generate_bug_title(description),
        description=description,
        severity=determine_severity(description),
        status="new",
        report_file_id=file_id,
        report_file_name=file_name,
    )

    session.add(bug)

    await session.commit()
    await session.refresh(bug)

    logger.info(
        "Создан баг #%s пользователем %s",
        bug.id,
        user_id,
    )

    return bug

async def update_bug(
    session: AsyncSession,
    bug_id: int,
    description: str,
    file_id: str,
    file_name: str,
):
    bug = await get_bug_by_id(
        session,
        bug_id,
    )

    if bug is None:
        return None

    bug.description = description
    bug.report_file_id = file_id
    bug.report_file_name = file_name

    bug.status = "reopened"

    await session.commit()
    await session.refresh(bug)

    return bug

async def get_bug_by_id(
    session,
    bug_id: int,
):
    result = await session.execute(
        select(BugReport)
        .where(BugReport.id == bug_id)
    )

    bug = result.scalar_one_or_none()

    if bug is None:
        logger.warning(
            "Баг #%s не найден",
            bug_id,
        )

    return bug

async def accept_bug(
    session,
    bug_id: int,
    admin_id: int,
    admin_username: str
):
    bug = await get_bug_by_id(
        session,
        bug_id
    )

    if bug is None:
        logger.warning(
            "Не удалось принять баг #%s: не найден",
            bug_id,
        )
        return None

    bug.assigned_admin_id =  admin_id
    bug.assigned_admin_username = admin_username
    bug.status = "in_progress"

    await session.commit()

    logger.info(
        "Баг #%s принят администратором %s (@%s)",
        bug_id,
        admin_id,
        admin_username,
    )

    return bug

async def get_bug_by_offset(
    session: AsyncSession,
    offset: int,
) -> BugReport | None:
    result = await session.execute(
        select(BugReport)
        .order_by(BugReport.created_at.desc())
        .offset(offset)
        .limit(1)
    )

    return result.scalar_one_or_none()

from sqlalchemy import func


async def get_bugs_count(
    session: AsyncSession,
) -> int:
    result = await session.execute(
        select(func.count(BugReport.id))
    )

    return result.scalar_one()

async def get_user_bug_by_offset(
    session: AsyncSession,
    user_id: int,
    offset: int,
) -> BugReport | None:
    result = await session.execute(
        select(BugReport)
        .where(BugReport.user_id == user_id)
        .order_by(BugReport.created_at.desc())
        .offset(offset)
        .limit(1)
    )

    return result.scalar_one_or_none()


async def get_user_bugs_count(
    session: AsyncSession,
    user_id: int,
) -> int:
    result = await session.execute(
        select(func.count(BugReport.id))
        .where(BugReport.user_id == user_id)
    )

    return result.scalar_one()

async def complete_bug_fix(
    session: AsyncSession,
    bug_id: int,
):
    bug = await get_bug_by_id(
        session,
        bug_id,
    )

    if bug is None:
        logger.warning(
            "Не удалось завершить баг #%s: не найден",
            bug_id,
        )
        return None

    bug.status = "waiting_confirmation"

    logger.info(
        "Баг #%s переведен в статус waiting_confirmation",
        bug_id,
    )

    await session.commit()
    await session.refresh(bug)

    return bug