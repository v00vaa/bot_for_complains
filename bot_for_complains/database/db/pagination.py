
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import BugReport, BugStatus

from .common import (
    BugView,
    _bug_view_from_row,
    _current_bug_stmt,
    _severity_order_expr,
)

async def get_bugs_page(
    session: AsyncSession,
    page: int,
    limit: int,
) -> list[BugView]:
    result = await session.execute(
        _current_bug_stmt()
        .order_by(_severity_order_expr(), BugReport.id.desc())
        .offset(page * limit)
        .limit(limit)
    )
    return [_bug_view_from_row(*row) for row in result.all()]

async def get_bug_page(
    session: AsyncSession,
    page: int,
    page_size: int,
) -> list[BugView]:
    return await get_bugs_page(
        session=session,
        page=page,
        limit=page_size,
    )

# не используется
async def get_bug_by_offset( 
    session: AsyncSession,
    offset: int,
) -> BugView | None:
    result = await session.execute(
        _current_bug_stmt()
        .order_by(_severity_order_expr(), BugReport.id.desc())
        .offset(offset)
        .limit(1)
    )
    row = result.one_or_none()
    return _bug_view_from_row(*row) if row else None

async def get_user_bug_by_offset(
    session: AsyncSession,
    user_id: int,
    offset: int,
) -> BugView | None:
    result = await session.execute(
        _current_bug_stmt()
        .where(BugReport.user_id == user_id)
        .order_by(BugReport.id.desc())
        .offset(offset)
        .limit(1)
    )
    row = result.one_or_none()
    return _bug_view_from_row(*row) if row else None

async def get_admin_bugs_page(
    session: AsyncSession,
    admin_id: int,
    page: int,
    limit: int,
) -> list[BugView]:
    result = await session.execute(
        _current_bug_stmt()
        .where(
            BugStatus.assigned_admin_id == admin_id,
            BugStatus.status == "in_progress",
        )
        .order_by(
            _severity_order_expr(),
            BugReport.id.desc(),
        )
        .offset(page * limit)
        .limit(limit)
    )

    return [
        _bug_view_from_row(*row)
        for row in result.all()
    ]

async def get_user_bug_page(
    session: AsyncSession,
    user_id: int,
    page: int,
    page_size: int,
) -> list[BugView]:
    result = await session.execute(
        _current_bug_stmt()
        .where(BugReport.user_id == user_id)
        .order_by(BugReport.id.desc())
        .offset(page * page_size)
        .limit(page_size)
    )

    return [_bug_view_from_row(*row) for row in result.all()]