"""
Функции постраничного получения обращений.

Назначение
----------
Модуль содержит запросы, используемые для формирования списков обращений,
отображаемых пользователям и администраторам.

Реализованы выборки:

    • общего списка обращений;
    • списка обращений пользователя;
    • списка обращений администратора;
    • получения обращения по смещению (служебные функции).

Во всех запросах используется _current_bug_stmt(), благодаря чему
возвращается только актуальное состояние каждого обращения
(последняя версия описания и последний статус).
"""
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
    """
    Возвращает страницу общего списка обращений.

    Список сортируется:

        1. по уровню критичности;
        2. по идентификатору обращения
           (новые обращения отображаются первыми).

    Используется администраторами при просмотре
    всех зарегистрированных обращений.
    """
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
    """
    Совместимый интерфейс получения страницы обращений.

    Представляет собой обертку над get_bugs_page(),
    сохранившую прежнее название функции.
    """
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
    """
    Возвращает обращение по абсолютному смещению.

    Использовалось в предыдущей реализации навигации.

    В текущей версии проекта не применяется
    """
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
    """
    Возвращает обращение пользователя
    по абсолютному смещению.

    Аналогично get_bug_by_offset(),
    использовалось старой системой навигации.
    """
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
    """
    Возвращает страницу обращений,
    назначенных конкретному администратору.

    В выборку попадают только обращения,
    находящиеся в статусе "in_progress".

    Сортировка выполняется сначала по критичности,
    затем по времени создания обращения.
    """
    # Показываем только обращения,
    # закрепленные за данным администратором.
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
    """
    Возвращает страницу обращений пользователя.

    Используется в личном кабинете пользователя
    для просмотра истории зарегистрированных обращений.

    Сначала отображаются наиболее новые обращения.
    """
    result = await session.execute(
        _current_bug_stmt()
        .where(BugReport.user_id == user_id)
        .order_by(BugReport.id.desc())
        .offset(page * page_size)
        .limit(page_size)
    )

    return [_bug_view_from_row(*row) for row in result.all()]