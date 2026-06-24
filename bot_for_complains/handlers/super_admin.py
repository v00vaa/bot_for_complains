from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from filters import IsSuperAdmin
from keyboards import get_super_admin_keyboard, get_remove_admin_keyboard, get_add_admin_keyboard
from services.roles import RolesStorage


super_admin_router = Router()

# Этот хэндлер срабатывает на команду /start администратора 
@super_admin_router.message(CommandStart(), IsSuperAdmin())
async def process_start_command(message: Message, i18n: dict[str, str]):
    
    await message.answer(
        text=i18n.get("/start_admin"),
        reply_markup=get_super_admin_keyboard(i18n)
    )

@super_admin_router.message(
    F.text == "Добавить администратора",
    IsSuperAdmin()
)
async def process_add_admin(
    message: Message,
    i18n: dict[str, str]
):
    await message.answer(
        i18n["choose_user_for_admin"],
        reply_markup=get_add_admin_keyboard(i18n)
    )

@super_admin_router.message(
    F.text == "Удалить администратора",
    IsSuperAdmin()
)
async def process_remove_admin(
    message: Message,
    i18n: dict[str, str]
):
    await message.answer(
        i18n["choose_admin_for_remove"],
        reply_markup=get_remove_admin_keyboard(i18n)
    )

@super_admin_router.message(
    F.user_shared,
    IsSuperAdmin()
)
async def process_user_shared(
    message: Message,
    roles: RolesStorage,
    i18n: dict[str, str]
):
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

    await message.answer(
        text,
        reply_markup=get_super_admin_keyboard(i18n)
    )