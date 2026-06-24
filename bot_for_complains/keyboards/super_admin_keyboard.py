from aiogram.types import (
    KeyboardButton,
    KeyboardButtonRequestUser,
    ReplyKeyboardMarkup,
)


def get_super_admin_keyboard(
    i18n: dict[str, str]
) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=i18n["bug_list"]
                )
            ],
            [
                KeyboardButton(
                    text=i18n["add_admin"]
                )
            ],
            [
                KeyboardButton(
                    text=i18n["remove_admin"]
                )
            ]
        ],
        resize_keyboard=True,
    )


def get_add_admin_keyboard(
    i18n: dict[str, str]
) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=i18n["select_admin"],
                    request_user=KeyboardButtonRequestUser(
                        request_id=1
                    )
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_remove_admin_keyboard(
    i18n: dict[str, str]
) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=i18n["select_admin_for_remove"],
                    request_user=KeyboardButtonRequestUser(
                        request_id=2
                    )
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )