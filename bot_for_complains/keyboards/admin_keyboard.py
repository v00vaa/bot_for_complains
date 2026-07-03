from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

def get_admin_keyboard(i18n: dict[str, str]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=i18n["bug_list"])]],
        resize_keyboard=True,
    )


def get_bug_details_keyboard(bug_id: int, i18n: dict[str, str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=i18n["details"], callback_data=f"bug_details:{bug_id}")]]
    )


def get_admin_bug_list_keyboard(
    bugs: list,
    page: int,
    has_prev: bool,
    has_next: bool,
    show_my_bugs: bool,
    i18n: dict[str, str],
) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text=f"#{bug.id} | {i18n.get(f'status_{bug.status}', bug.status)}",
                callback_data=f"bug_details:{bug.id}",
            )
        ]
        for bug in bugs
    ]

    # Кнопка переключения режима
    keyboard.append([
        InlineKeyboardButton(
            text=(
                i18n["all_bugs"]
                if show_my_bugs
                else i18n["my_bugs"]
            ),
            callback_data=(
                f"all_bug_page:0"
                if show_my_bugs
                else f"my_bug_page:0"
            ),
        )
    ])

    navigation_row = []

    if has_prev:
        navigation_row.append(
            InlineKeyboardButton(
                text=i18n["backward"],
                callback_data=(
                    f"{'my_bug_page' if show_my_bugs else 'all_bug_page'}:{page - 1}"
                ),
            )
        )

    if has_next:
        navigation_row.append(
            InlineKeyboardButton(
                text=i18n["forward"],
                callback_data=(
                    f"{'my_bug_page' if show_my_bugs else 'all_bug_page'}:{page + 1}"
                ),
            )
        )

    if navigation_row:
        keyboard.append(navigation_row)

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )


def get_bug_card_keyboard(
    bug_id: int,
    version: int,
    oldest_version: int,
    newest_version: int,
    is_assigned_admin: bool,
    i18n: dict[str, str],
    is_training_sample: bool,
) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text=i18n["report_file"], callback_data=f"report_file:{bug_id}:{version}")],
        [InlineKeyboardButton(text=i18n["accept"], callback_data=f"accept_bug:{bug_id}")],
    ]

    if not is_assigned_admin:
        keyboard.append([
            InlineKeyboardButton(
                text=i18n["invalid_description"],
                callback_data=f"invalid_bug:{bug_id}",
            )
        ])
    if not is_training_sample:
        keyboard.append([
            InlineKeyboardButton(
                text=i18n["mark_valid"],
                callback_data=f"training_add:{bug_id}:{version}",
            )
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(
                text=i18n["mark_invalid"],
                callback_data=f"training_remove:{bug_id}:{version}",
            )
        ])

    if is_assigned_admin:
        keyboard.append([InlineKeyboardButton(text=i18n["complete_fix"], callback_data=f"complete_fix:{bug_id}")])

    keyboard.extend(
        [
            [
                InlineKeyboardButton(text=i18n["severity_not_set"], callback_data=f"set_severity:{bug_id}:not_set"),
                InlineKeyboardButton(text=i18n["severity_critical"], callback_data=f"set_severity:{bug_id}:critical"),
            ],
            [
                InlineKeyboardButton(text=i18n["severity_high"], callback_data=f"set_severity:{bug_id}:high"),
                InlineKeyboardButton(text=i18n["severity_medium"], callback_data=f"set_severity:{bug_id}:medium"),
                InlineKeyboardButton(text=i18n["severity_low"], callback_data=f"set_severity:{bug_id}:low"),
            ],
        ]
    )

    navigation_row = []
    if version < newest_version:
        navigation_row.append(
            InlineKeyboardButton(text=i18n["newer_version"], callback_data=f"bug_version:{bug_id}:{version + 1}")
        )
    if version > oldest_version:
        navigation_row.append(
            InlineKeyboardButton(text=i18n["older_version"], callback_data=f"bug_version:{bug_id}:{version - 1}")
        )
    if navigation_row:
        keyboard.append(navigation_row)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_bug_notification_keyboard(
    bug_id: int,
    i18n: dict[str, str],
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n["details"],
                    callback_data=f"bug_details:{bug_id}",
                )
            ]
        ]
    )