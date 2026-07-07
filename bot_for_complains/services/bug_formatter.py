"""
Модуль форматирования карточек обращений.

Здесь находятся функции, преобразующие объекты BugView
в готовый HTML-текст для Telegram.

Вынесение форматирования в отдельный модуль позволяет:

• не смешивать бизнес-логику и оформление сообщений;
• использовать один шаблон сразу во всех хэндлерах;
• изменять внешний вид карточек в одном месте.
"""
from typing import Any


def get_status_text(
    bug: Any,
    i18n: dict[str, str],
) -> str:
    """
    Возвращает красивое текстовое представление статуса.

    Для статуса "В работе" дополнительно отображается
    администратор, которому назначено обращение.

    Пример:

        В работе у @admin

    Для остальных статусов используется перевод из словаря.
    """
    if bug.status == "in_progress" and bug.assigned_admin_username:
        return (
            f"{i18n['status_in_progress']} "
            f"{i18n['status_assigned_to']} @{bug.assigned_admin_username}"
        )

    return i18n.get(f"status_{bug.status}", bug.status)


def get_severity_text(
    severity: str,
    i18n: dict[str, str],
) -> str:
    """
    Преобразует внутренний код критичности
    в читаемый текст.

    Например:

        critical -> Критическая
        low -> Низкая
    """
    return i18n.get(f"severity_{severity}", severity)


def format_bug_card(
    bug: Any,
    i18n: dict[str, str],
) -> str:
    """
    Формирует полную карточку обращения
    для администратора.

    Содержит:

    • номер обращения;
    • версию;
    • описание;
    • критичность;
    • текущий статус;
    • имя прикреплённого отчёта;
    • ссылку на пользователя.

    Используется практически во всех административных
    обработчиках.
    """
    status_text = get_status_text(bug, i18n)
    severity_text = get_severity_text(bug.severity, i18n)

    return (
        f"<b>{i18n['bug_number']} #{bug.id}</b>\n"
        f"{i18n['version']}: {bug.version}\n\n"
        f"{i18n['description']}:\n"
        f"{bug.description}\n\n"
        f"{i18n['severity']}: {severity_text}\n"
        f"{i18n['status']}: {status_text}\n\n"
        f"{i18n['report']}: {bug.report_file_name}\n\n"
        f"{i18n['user']}: "
        f"<a href='tg://user?id={bug.user_id}'>{bug.user_id}</a>"
    )


def format_user_bug_card(
    bug: Any,
    i18n: dict[str, str],
) -> str:
    """
    Формирует сокращённую карточку обращения
    для обычного пользователя.

    В отличие от административной карточки
    здесь отсутствует информация:

    • о критичности;
    • о назначенном администраторе;
    • о внутренних служебных данных.

    Пользователь видит только сведения,
    относящиеся к его обращению.
    """
    status_text = get_status_text(bug, i18n)

    return (
        f"<b>{i18n['bug_number']} #{bug.id}</b>\n\n"
        f"{i18n['description']}:\n"
        f"{bug.description}\n\n"
        f"{i18n['status']}: {status_text}\n\n"
        f"{i18n['report']}: {bug.report_file_name}"
    )

