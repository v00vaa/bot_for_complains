"""
Клавиатуры суперадминистратора.

Суперадминистратор имеет доступ к управлению администраторами
и просмотру всех зарегистрированных обращений.

В отличие от обычных администраторов используется одна постоянная
клавиатура, содержащая как основные действия, так и кнопки выбора
пользователей через механизм request_user Telegram.
"""

from aiogram.types import (
    KeyboardButton,
    KeyboardButtonRequestUser,
    ReplyKeyboardMarkup,
)


def get_super_admin_keyboard(
    i18n: dict[str, str]
) -> ReplyKeyboardMarkup:
    """
    Главное меню суперадминистратора.

    Содержит:
        • просмотр списка обращений;
        • выбор пользователя для назначения администратором;
        • выбор администратора для удаления.

    Кнопки "Добавить" и "Удалить" сразу открывают системный
    диалог выбора пользователя Telegram через request_user.
    Благодаря этому отдельные промежуточные клавиатуры
    больше не требуются.
    """

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=i18n["bug_list"]
                )
            ],
            [
                KeyboardButton(
                    text=i18n["add_admin"],
                    request_user=KeyboardButtonRequestUser(
                        request_id=1,
                    ),
                )
            ],
            [
                KeyboardButton(
                    text=i18n["remove_admin"],
                    request_user=KeyboardButtonRequestUser(
                        request_id=2,
                    ),
                )
            ],
        ],
        resize_keyboard=True,
    )