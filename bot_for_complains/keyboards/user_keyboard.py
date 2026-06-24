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
    status: str,
    index: int,
    has_prev: bool,
    has_next: bool,
    i18n: dict[str, str],
) -> InlineKeyboardMarkup:

    keyboard = []

    navigation_row = []

    if has_prev:
        navigation_row.append(
            InlineKeyboardButton(
                text=i18n["backward"],
                callback_data=f"user_bug_prev:{index}",
            )
        )

    if has_next:
        navigation_row.append(
            InlineKeyboardButton(
                text=i18n["forward"],
                callback_data=f"user_bug_next:{index}",
            )
        )

    if navigation_row:
        keyboard.append(navigation_row)

    if status == "waiting_confirmation":
        keyboard.extend([
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
        ])

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )