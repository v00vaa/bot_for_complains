"""
Функции изменения состояния обращений.

Назначение
----------
Модуль содержит операции, изменяющие жизненный цикл обращения.

В системе отсутствует изменение существующих записей BugStatus.
Любое изменение состояния оформляется созданием новой записи истории,
что позволяет полностью восстановить последовательность всех действий
над обращением.

Здесь реализованы операции:

    • принятие обращения в работу;
    • завершение исправления;
    • окончательное закрытие обращения;
    • повторное открытие обращения;
    • изменение критичности;
    • пометка обращения как имеющего некорректное описание;
    • управление выборкой данных для обучения модели.

Благодаря такому подходу сохраняется полный журнал изменений,
который может использоваться как для отображения истории пользователю,
так и для последующего анализа.
"""
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

async def accept_bug(
    session: AsyncSession,
    bug_id: int,
    admin_id: int,
    admin_username: str | None,
) -> BugView | None:
    """
    Переводит обращение в статус "in_progress".

    Вызывается, когда администратор принимает обращение в работу.

    При этом создается новая запись истории статусов,
    содержащая информацию о назначенном администраторе.

    Возвращает актуальное состояние обращения либо None,
    если обращение отсутствует.
    """
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
    """
    Переводит обращение в статус ожидания подтверждения пользователя.

    Используется после завершения исправления администратором.

    Назначенный администратор сохраняется,
    чтобы информация об ответственном сотруднике
    не терялась при смене статуса.
    """
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
    """
    Полностью закрывает обращение.

    Вызывается после подтверждения пользователем,
    что проблема действительно устранена.

    Создает новую запись истории со статусом "closed".
    """
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
    """
    Повторно открывает обращение.

    Используется, когда пользователь сообщает,
    что проблема после исправления осталась.

    Следующее описание проблемы будет сохранено
    как новая версия BugData.
    """
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
    """
    Изменяет уровень критичности обращения.

    В системе критичность хранится вместе со статусом,
    поэтому изменение критичности также оформляется
    новой записью BugStatus.

    Остальные параметры последнего состояния
    (статус и назначенный администратор)
    автоматически сохраняются.
    """
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
    """
    Помечает обращение как имеющее недостаточно информативное описание.

    Используется администратором, если описание проблемы
    не позволяет воспроизвести ошибку.

    После изменения статуса пользователю предлагается
    повторно описать проблему более подробно.
    """
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
    """
    Изменяет признак использования версии обращения
    в обучающей выборке модели описаний.

    Флаг хранится в BugData, поскольку каждая версия
    обращения может независимо участвовать
    или не участвовать в обучении модели.

    Возвращает:

        True  — значение изменилось;
        False — запись отсутствует либо флаг уже имел нужное значение.

    Возвращаемое значение используется планировщиком обучения,
    чтобы запускать переобучение модели только при реальном
    изменении обучающей выборки.
    """
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