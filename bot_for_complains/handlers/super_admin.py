"""
Роутер суперадминистратора.

Содержит обработчики, доступные только главному администратору:

    • запуск бота;
    • назначение новых администраторов;
    • удаление администраторов.

Выбор пользователей выполняется средствами Telegram через
KeyboardButtonRequestUser, поэтому отдельные сценарии выбора
пользователя отсутствуют.
"""

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from filters import IsSuperAdmin
from keyboards import get_super_admin_keyboard
from services.roles import RolesStorage


super_admin_router = Router()


@super_admin_router.message(
    CommandStart(),
    IsSuperAdmin(),
)
async def process_start_command(
    message: Message,
    i18n: dict[str, str],
):
    """
    Отправляет главное меню суперадминистратора.
    """

    await message.answer(
        text=i18n["/start_admin"],
        reply_markup=get_super_admin_keyboard(i18n),
    )


@super_admin_router.message(
    F.user_shared,
    IsSuperAdmin(),
)
async def process_user_shared(
    message: Message,
    roles: RolesStorage,
    i18n: dict[str, str],
):
    """
    Обрабатывает пользователя, выбранного через request_user.

    request_id определяет действие:

        1 — добавить администратора;
        2 — удалить администратора.

    После выполнения операции пользователю снова отображается
    основное меню.
    """

    request_id = message.user_shared.request_id
    user_id = message.user_shared.user_id

    if request_id == 1:
        text = (
            i18n["admin_added"]
            if roles.add_admin(user_id)
            else i18n["already_admin"]
        )

    elif request_id == 2:
        text = (
            i18n["admin_removed"]
            if roles.remove_admin(user_id)
            else i18n["not_admin"]
        )

    else:
        return

    await message.answer(
        text,
        reply_markup=get_super_admin_keyboard(i18n),
    )