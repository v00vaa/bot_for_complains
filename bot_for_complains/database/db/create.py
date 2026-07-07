"""
Функции создания новых обращений и их состояний.

Назначение
----------
Модуль инкапсулирует логику первоначального создания обращения в базе
данных. При регистрации нового бага создаются записи сразу в нескольких
таблицах, каждая из которых отвечает за собственную часть информации.

Процесс создания обращения состоит из следующих этапов:

    1. Создается запись BugReport.
       Содержит неизменяемую информацию об обращении
       (автор, дата создания, заголовок).

    2. Создается первая версия BugData.
       Содержит описание проблемы и приложенный пользователем файл.

    3. Создается первая запись BugStatus.
       Фиксирует текущее состояние обращения ("new")
       и начальную критичность.

После успешного создания всех записей изменения фиксируются одной
транзакцией, что гарантирует целостность данных.
"""
import logging

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
    get_actual_version,
)

logger = logging.getLogger(__name__)

async def create_bug(
    session: AsyncSession,
    user_id: int,
    description: str,
    file_id: str,
    file_name: str,
) -> BugView:
    """
    Создает новое обращение.

    Помимо записи самого обращения автоматически создаются:

        • первая версия BugData;
        • первый статус BugStatus.

    После успешного завершения возвращается объект BugView,
    содержащий актуальное состояние созданного обращения.
    """
    # Создание основной записи обращения.
    bug = BugReport(
        user_id=user_id,
        title=generate_bug_title(description),
    )
    session.add(bug)
    await session.flush()
    # Создание первой версии описания обращения.
    data = BugData(
        bug_id=bug.id,
        version=1,
        description=description,
        report_file_id=file_id,
        report_file_name=file_name,
    )
    session.add(data)
    await session.flush()
    # Создание первоначального статуса.
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
    """
    Создает новую запись истории статусов.

    Если критичность явно не указана,
    она наследуется от предыдущего состояния обращения.
    """
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

async def update_bug(
    session: AsyncSession,
    bug_id: int,
    description: str,
    file_id: str,
    file_name: str,
) -> BugView | None:
    """
    Создает новую версию существующего обращения.

    Данная функция используется при повторном открытии обращения
    пользователем после того, как администратор отметил его как
    исправленное.

    В отличие от обычного обновления записи:

        • предыдущие версии обращения не изменяются;
        • создается новая запись BugData с увеличенным номером версии;
        • создается новая запись BugStatus со статусом "reopened".

    Благодаря этому сохраняется полная история изменений обращения,
    включая все предыдущие описания и приложенные пользователем файлы.

    Возвращает актуальное представление обращения (BugView) либо None,
    если обращение не найдено.
    """
    bug = await session.get(BugReport, bug_id)
    current_data = await get_actual_version(session, bug_id)
    last_status = await get_actual_status(session, bug_id)

    if bug is None or current_data is None:
        return None
    # Создаем новую версию описания
    data = BugData(
        bug_id=bug_id,
        version=current_data.version + 1,
        description=description,
        report_file_id=file_id,
        report_file_name=file_name,
    )
    session.add(data)
    await session.flush()
    # Фиксируем повторное открытие обращения.
    # Критичность наследуется от предыдущего статуса.
    status = await create_status(
        session=session,
        bug_id=bug_id,
        bug_data_id=data.id,
        status="reopened",
        severity=last_status.severity if last_status else SEVERITY_NOT_SET,
    )

    await session.commit()
    return _bug_view_from_row(bug, data, status)
