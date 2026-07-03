from typing import Any


def get_status_text(
    bug: Any,
    i18n: dict[str, str],
) -> str:
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
    return i18n.get(f"severity_{severity}", severity)


def format_bug_card(
    bug: Any,
    i18n: dict[str, str],
) -> str:
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
    status_text = get_status_text(bug, i18n)

    return (
        f"<b>{i18n['bug_number']} #{bug.id}</b>\n\n"
        f"{i18n['description']}:\n"
        f"{bug.description}\n\n"
        f"{i18n['status']}: {status_text}\n\n"
        f"{i18n['report']}: {bug.report_file_name}"
    )


def format_bug_short(
    bug: Any,
    i18n: dict[str, str],
) -> str:
    return (
        f"#{bug.id} | "
        f"{get_status_text(bug, i18n)}"
    )


def format_bug_history(
    versions: list[Any],
    i18n: dict[str, str],
) -> str:
    if not versions:
        return i18n["history_empty"]

    rows = [
        f"v{version.version}: {version.report_file_name}"
        for version in versions
    ]
    return "\n".join(rows)
