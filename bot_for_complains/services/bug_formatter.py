from database.models import BugReport


def get_status_text(
    bug,
    i18n: dict[str, str],
) -> str:
    if (
        bug.status == "in_progress"
        and bug.assigned_admin_username
    ):
        return (
            f"{i18n['status_in_progress']} "
            f"у @{bug.assigned_admin_username}"
        )

    return i18n.get(
        f"status_{bug.status}",
        bug.status,
    )

def format_bug_card(
    bug: BugReport,
    i18n: dict[str, str],
) -> str:
    status_text = get_status_text(
        bug,
        i18n,
    )

    return (
        f"<b>{bug.title}</b>\n\n"
        f"{i18n['description']}:\n"
        f"{bug.description}\n\n"
        f"{i18n['severity']}: "
        f"{bug.severity}\n"
        f"{i18n['status']}: "
        f"{status_text}\n\n"
        f"{i18n['report']}: "
        f"{bug.report_file_name}\n\n"
        f"{i18n['user']}: "
        f"<a href='tg://user?id={bug.user_id}'>"
        f"{bug.user_id}"
        f"</a>"
    )

def format_user_bug_card(bug, i18n: dict[str, str],) -> str:
    status_text = get_status_text(bug, i18n)
    return (
        f"<b>{bug.title}</b>\n\n"
        f"{i18n['description']}:\n"
        f"{bug.description}\n\n"
        f"{i18n['status']}: "
        f"{status_text}\n\n"
        f"{i18n['report']}: "
        f"{bug.report_file_name}\n\n"
    )
