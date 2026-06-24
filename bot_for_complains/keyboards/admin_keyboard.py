from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def get_admin_keyboard(i18n: dict[str, str]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=i18n["bug_list"]
                )
            ]
        ],
        resize_keyboard=True,
    )

def get_bug_details_keyboard(
    bug_id: int,
    i18n: dict[str, str]
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n["details"],
                    callback_data=f"bug_details:{bug_id}"
                )
            ]
        ]
    )

def get_bug_card_keyboard(bug_id: int, i18n: dict[str, str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n["accept"],
                    callback_data=f"accept_bug:{bug_id}"
                )
            ]
        ]
    )

def get_bug_list_keyboard(
    bug_id: int,
    index: int,
    has_prev: bool,
    has_next: bool,
    is_assigned_admin: bool,
    i18n: dict[str, str],
) -> InlineKeyboardMarkup:

    keyboard = []

    navigation_row = []

    if has_prev:
        navigation_row.append(
            InlineKeyboardButton(
                text=i18n["backward"],
                callback_data=f"bug_prev:{index}",
            )
        )

    if has_next:
        navigation_row.append(
            InlineKeyboardButton(
                text=i18n["forward"],
                callback_data=f"bug_next:{index}",
            )
        )

    if navigation_row:
        keyboard.append(
            navigation_row
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                text=i18n["report_file"],
                callback_data=f"report_file:{bug_id}",
            )
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                text=i18n["accept"],
                callback_data=f"accept_bug:{bug_id}",
            )
        ]
    )

    if is_assigned_admin:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=i18n["complete_fix"],
                    callback_data=f"complete_fix:{bug_id}",
                )
            ]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )