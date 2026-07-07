"""
Функции получения данных из базы.

Назначение
----------
Модуль содержит запросы, используемые для чтения информации
об обращениях без изменения состояния базы данных.

Здесь реализованы функции получения:

    • последней версии обращения;
    • текущего статуса обращения;
    • актуального состояния обращения;
    • конкретной версии обращения;
    • полной истории версий;
    • обучающей выборки для модели описаний.

Модуль используется обработчиками Telegram-бота, а также
другими слоями приложения при необходимости получить данные
о текущем или историческом состоянии обращения.
"""
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
    """
    Возвращает последнюю версию данных обращения.

    В системе описание обращения не изменяется,
    а создается новая запись BugData с увеличенным номером версии.

    Используется перед созданием очередной версии
    или для отображения пользователю последнего описания.
    """
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
    """
    Возвращает последний статус обращения.

    История статусов хранится полностью,
    поэтому текущим считается статус,
    созданный последним.

    При одинаковом времени создания дополнительно
    используется сортировка по идентификатору записи.
    """
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
    """
    Возвращает актуальное состояние обращения.

    Использует общий SQL-запрос _current_bug_stmt(),
    который автоматически объединяет:

        • BugReport;
        • последнюю версию BugData;
        • последний BugStatus.

    Возвращает объект BugView либо None,
    если обращение отсутствует.
    """
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
    """
    Возвращает конкретную версию обращения.

    Используется при просмотре истории изменений,
    когда пользователь или администратор
    переключается между версиями обращения.

    Для выбранной версии отображается последний статус,
    относящийся именно к этой версии.
    Если такой статус отсутствует,
    используется текущий статус обращения.
    """
    # Получаем основную информацию об обращении.
    bug = await session.get(BugReport, bug_id)
    # Загружаем требуемую версию описания.
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
    # Для выбранной версии ищем соответствующий статус.
    result = await session.execute(
        select(BugStatus)
        .where(BugStatus.bug_data_id == data.id)
        .order_by(BugStatus.created_at.desc(), BugStatus.id.desc())
        .limit(1)
    )
    # Если отдельного статуса нет,
    # используем последнее состояние обращения.
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
    """
    Возвращает все сохраненные версии обращения.

    История загружается через отношение ORM (versions)
    и используется при необходимости анализа
    всех изменений обращения.
    """
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
    """
    Возвращает описания, входящие в обучающую выборку модели.

    В выборку включаются только версии обращений,
    для которых установлен флаг is_training_sample.

    Используется при обучении модели описаний
    как при запуске приложения, так и во время
    последующего переобучения.
    """
    result = await session.execute(
        select(BugData.description)
        .where(BugData.is_training_sample.is_(True))
    )

    return result.scalars().all()