"""
Функции подсчета количества обращений и вычисления числа страниц.

Модуль используется при построении постраничной навигации как
для пользователей, так и для администраторов. Также содержит
служебные функции подсчета количества версий обращения и количества
обращений, назначенных конкретному администратору.

Все функции возвращают только числовые значения и не загружают
полные объекты обращений из базы данных
"""
from math import ceil

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import BugData, BugReport
from .common import _current_bug_stmt

async def get_bugs_count(session: AsyncSession) -> int:
    """
    Возвращает общее количество зарегистрированных обращений.

    Используется при построении общего списка обращений
    и расчете количества страниц.
    """
    result = await session.execute(select(func.count(BugReport.id)))
    return result.scalar_one()

async def get_user_bugs_count(
    session: AsyncSession,
    user_id: int,
) -> int:
    """
    Возвращает количество обращений конкретного пользователя.

    Используется при отображении истории обращений пользователя
    и вычислении количества страниц в его личном списке.
    """
    result = await session.execute(
        select(func.count(BugReport.id)).where(BugReport.user_id == user_id)
    )
    return result.scalar_one()

async def get_bug_versions_count(
    session: AsyncSession,
    bug_id: int,
) -> int:
    """
    Возвращает количество сохранённых версий обращения.

    Каждое повторное открытие обращения создает новую запись BugData,
    поэтому количество записей соответствует числу версий.
    Используется для кнопок "старее"/"новее".
    """
    result = await session.execute(
        select(func.count(BugData.id)).where(BugData.bug_id == bug_id)
    )
    return result.scalar_one()

async def get_admin_bugs_count(
    session: AsyncSession,
    admin_id: int,
) -> int:
    """
    Возвращает количество обращений,
    находящихся в работе у администратора.

    Для подсчета используется только актуальное состояние каждого
    обращения (_current_bug_stmt), поэтому архивные статусы
    и предыдущие версии не учитываются.
    """
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
    """
    Вычисляет количество страниц общего списка обращений.

    page_size — количество элементов,
    отображаемых на одной странице.
    """
    total = await get_bugs_count(session)

    if total == 0:
        return 0

    return ceil(total / page_size)

async def get_user_bug_page_count(
    session: AsyncSession,
    user_id: int,
    page_size: int,
) -> int:
    """
    Вычисляет количество страниц списка обращений пользователя.

    Используется для построения постраничной навигации
    в пользовательском интерфейсе.
    """
    total = await get_user_bugs_count(
        session,
        user_id,
    )

    return ceil(total / page_size) if total else 0