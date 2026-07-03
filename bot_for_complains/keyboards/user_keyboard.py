from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def get_user_keyboard(i18n: dict[str, str]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=i18n["report_bt"]
                )
            ],
            [
                KeyboardButton(
                    text=i18n["status_bt"]
                )
            ]
        ],
        resize_keyboard=True,
    )

def get_bug_confirmation_keyboard(
    bug_id: int,
    i18n: dict[str, str],
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n["confirm"],
                    callback_data=f"bug_confirm:{bug_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n["not_confirm"],
                    callback_data=f"bug_reject:{bug_id}",
                )
            ]
        ]
    )

def get_user_bug_keyboard(
    bug_id: int,
    version: int,
    versions_count: int,
    status: str,
    i18n: dict[str, str],
) -> InlineKeyboardMarkup:

    keyboard = []

    navigation = []

    if version > 1:
        navigation.append(
            InlineKeyboardButton(
                text=i18n["backward"],
                callback_data=f"user_bug_version_prev:{bug_id}:{version}",
            )
        )

    if version < versions_count:
        navigation.append(
            InlineKeyboardButton(
                text=i18n["forward"],
                callback_data=f"user_bug_version_next:{bug_id}:{version}",
            )
        )

    if navigation:
        keyboard.append(navigation)

    if status == "waiting_confirmation":
        keyboard.extend(
            [
                [
                    InlineKeyboardButton(
                        text=i18n["confirm"],
                        callback_data=f"bug_confirm:{bug_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=i18n["not_confirm"],
                        callback_data=f"bug_reject:{bug_id}",
                    )
                ],
            ]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard,
    )

def get_user_bug_list_keyboard(
    bugs: list,
    page: int,
    has_prev: bool,
    has_next: bool,
    i18n: dict[str, str],
) -> InlineKeyboardMarkup:

    keyboard = [
        [
            InlineKeyboardButton(
                text=f"#{bug.id} | {i18n.get(f'status_{bug.status}', bug.status)}",
                callback_data=f"user_bug_details:{bug.id}",
            )
        ]
        for bug in bugs
    ]

    navigation = []

    if has_prev:
        navigation.append(
            InlineKeyboardButton(
                text=i18n["backward"],
                callback_data=f"user_bug_page:{page-1}",
            )
        )

    if has_next:
        navigation.append(
            InlineKeyboardButton(
                text=i18n["forward"],
                callback_data=f"user_bug_page:{page+1}",
            )
        )

    if navigation:
        keyboard.append(navigation)

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )

def get_user_bug_list_keyboard(
    bugs: list,
    page: int,
    has_prev: bool,
    has_next: bool,
    i18n: dict[str, str],
) -> InlineKeyboardMarkup:

    keyboard = [
        [
            InlineKeyboardButton(
                text=f"#{bug.id} | {i18n.get(f'status_{bug.status}', bug.status)}",
                callback_data=f"user_bug_details:{bug.id}",
            )
        ]
        for bug in bugs
    ]

    navigation = []

    if has_prev:
        navigation.append(
            InlineKeyboardButton(
                text=i18n["backward"],
                callback_data=f"user_bug_page:{page-1}",
            )
        )

    if has_next:
        navigation.append(
            InlineKeyboardButton(
                text=i18n["forward"],
                callback_data=f"user_bug_page:{page+1}",
            )
        )

    if navigation:
        keyboard.append(navigation)

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )

def get_cancel_keyboard(
    i18n: dict[str, str],
) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=i18n["cancel"],
                )
            ]
        ],
        resize_keyboard=True,
    )

def get_bug_invalid_keyboard(
    bug_id: int,
    i18n: dict[str, str],
):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n["rewrite_description"],
                    callback_data=f"rewrite_bug:{bug_id}",
                )
            ]
        ]
    )