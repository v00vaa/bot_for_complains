import logging

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from filters import IsAdmin, TextKeyFilter
from keyboards import get_bug_card_keyboard, get_admin_keyboard, get_bug_list_keyboard, get_bug_confirmation_keyboard
from database import get_bug_by_id, accept_bug, get_bug_by_offset, get_bugs_count, complete_bug_fix
from services import format_bug_card

logger = logging.getLogger(__name__)

admin_router = Router()

# Этот хэндлер срабатывает на команду /start администратора 
@admin_router.message(CommandStart(), IsAdmin())
async def process_start_command(message: Message, i18n: dict[str, str]):
    
    await message.answer(
        text=i18n.get("/start_admin"),
        reply_markup=get_admin_keyboard(i18n)
    )

@admin_router.callback_query(
    F.data.startswith("bug_details:"),
    IsAdmin()
)
async def process_bug_details(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: dict[str, str],
):
    bug_id = int(
        callback.data.split(":")[1]
    )

    logger.info(
        "Администратор %s запросил детали бага #%s",
        callback.from_user.id,
        bug_id,
    )

    bug = await get_bug_by_id(
        session,
        bug_id,
    )

    if bug is None:
        logger.warning(
            "Баг #%s не найден при просмотре администратором %s",
            bug_id,
            callback.from_user.id,
        )

        await callback.answer(
            i18n["bug_not_found"],
            show_alert=True,
        )
        return

    if bug.report_file_id:
        await callback.bot.send_document(
            chat_id=callback.from_user.id,
            document=bug.report_file_id,
        )

    await callback.message.answer(
        text=format_bug_card(
            bug,
            i18n,
        ),
        reply_markup=get_bug_card_keyboard(
            bug.id,
            i18n,
        ),
    )

    await callback.answer()

# Этот хэндлер срабатывает на кнопку "Принимаю в работу"
@admin_router.callback_query(
    F.data.startswith("accept_bug:"),
    IsAdmin()
)
async def process_accept_bug(
    callback: CallbackQuery,
    session,
    i18n: dict[str, str]
):
    bug_id = int(callback.data.split(":")[1])

    logger.info(
        "Администратор %s пытается взять баг #%s в работу",
        callback.from_user.id,
        bug_id,
    )

    bug = await accept_bug(
        session=session,
        bug_id=bug_id,
        admin_id=callback.from_user.id,
        admin_username=callback.from_user.username
    )

    if bug is None:
        logger.warning(
            "Не удалось назначить баг #%s: не найден",
            bug_id,
        )

        await callback.answer(
            i18n.get("bug_not_found", "Баг не найден"),
            show_alert=True
        )
        return

    logger.info(
        "Баг #%s назначен администратору %s (@%s)",
        bug.id,
        callback.from_user.id,
        callback.from_user.username,
    )

    await callback.message.edit_text(
        text=format_bug_card(
            bug,
            i18n,
        )
    )

    await callback.answer(
        i18n["bug_accepted"]
    )

    await callback.answer()

# Этот хэндлер срабатывает на кнопку "список багов"
@admin_router.message(
    TextKeyFilter("bug_list"),
    IsAdmin()
)
async def process_bug_list(
    message: Message,
    session: AsyncSession,
    i18n: dict[str, str],
):
    logger.info(
        "Администратор %s открыл список багов",
        message.from_user.id,
    )
    bug = await get_bug_by_offset(
        session,
        0,
    )

    if bug is None:
        logger.info(
            "Список багов пуст"
        )

        await message.answer(
            i18n["no_bugs_admin"]
        )
        return

    total = await get_bugs_count(
        session
    )

    await message.answer(
        text=format_bug_card(bug, i18n),
        reply_markup=get_bug_list_keyboard(
            bug_id=bug.id,
            index=0,
            has_prev=False,
            has_next=total > 1,
            is_assigned_admin=(
                bug.assigned_admin_id == message.from_user.id and bug.status == "in_progress"
            ),
            i18n=i18n,
        )
    )

# Этот хэндлер срабатывает на кнопку ">>" в списке багов 
@admin_router.callback_query(
    F.data.startswith("bug_next:"),
    IsAdmin()
)
async def process_next_bug(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: dict[str, str],
):
    current_index = int(
        callback.data.split(":")[1]
    )

    next_index = current_index + 1

    logger.debug(
        "Администратор %s перешел к багу с индексом %s",
        callback.from_user.id,
        next_index,
    )

    bug = await get_bug_by_offset(
        session,
        next_index,
    )

    if bug is None:
        await callback.answer()
        return

    total = await get_bugs_count(
        session
    )

    await callback.message.edit_text(
        text=format_bug_card(bug, i18n),
        reply_markup=get_bug_list_keyboard(
            bug_id=bug.id,
            index=next_index,
            has_prev=next_index > 0,
            has_next=next_index < total - 1,
            is_assigned_admin=(
                bug.assigned_admin_id == callback.from_user.id and bug.status == "in_progress"
            ),
            i18n=i18n,
        )
    )

    await callback.answer()

# Этот хэндлер срабатывает на кнопку 
@admin_router.callback_query(
    F.data.startswith("bug_prev:"),
    IsAdmin()
)
async def process_prev_bug(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: dict[str, str],
):
    current_index = int(
        callback.data.split(":")[1]
    )

    prev_index = current_index - 1

    logger.debug(
        "Администратор %s вернулся к багу с индексом %s",
        callback.from_user.id,
        prev_index,
    )

    if prev_index < 0:
        await callback.answer()
        return

    bug = await get_bug_by_offset(
        session,
        prev_index,
    )

    total = await get_bugs_count(
        session
    )

    await callback.message.edit_text(
        text=format_bug_card(bug, i18n),
        reply_markup=get_bug_list_keyboard(
            bug_id=bug.id,
            index=prev_index,
            has_prev=prev_index > 0,
            has_next=prev_index < total - 1,
            is_assigned_admin=(
                bug.assigned_admin_id == callback.from_user.id and bug.status == "in_progress"
            ),
            i18n=i18n,
        )
    )

    await callback.answer()

# Этот хэндлер срабатывает на  кнопку 
@admin_router.callback_query(
    F.data.startswith("report_file:"),
    IsAdmin()
)
async def process_report_file(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: dict[str, str]
):
    bug_id = int(
        callback.data.split(":")[1]
    )

    logger.info(
        "Администратор %s запросил файл отчета для бага #%s",
        callback.from_user.id,
        bug_id,
    )

    bug = await get_bug_by_id(
        session,
        bug_id,
    )

    if not bug:
        logger.warning(
        "Баг #%s не найден при просмотре администратором %s отчета",
        bug_id,
        callback.from_user.id,
    )

        await callback.answer(
            i18n.get("bug_not_found", "Баг не найден"),
            show_alert=True,
        )
        return

    await callback.bot.send_document(
        chat_id=callback.from_user.id,
        document=bug.report_file_id,
    )

    logger.info(
        "Файл '%s' по багу #%s отправлен администратору %s",
        bug.report_file_name,
        bug.id,
        callback.from_user.id,
    )

    await callback.answer()

# Этот хэндлер срабатывает на кнопку 
@admin_router.callback_query(
    F.data.startswith("complete_fix:"),
    IsAdmin()
)
async def process_complete_fix(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: dict[str, str],
):
    bug_id = int(
        callback.data.split(":")[1]
    )

    logger.info(
        "Администратор %s завершает исправление бага #%s",
        callback.from_user.id,
        bug_id,
    )

    bug = await get_bug_by_id(
        session,
        bug_id,
    )

    if bug is None:
        await callback.answer(
            i18n["bug_not_found"],
            show_alert=True,
        )
        return

    if bug.assigned_admin_id != callback.from_user.id:
        logger.warning(
            "Администратор %s попытался завершить чужой баг #%s. Назначен: %s",
            callback.from_user.id,
            bug_id,
            bug.assigned_admin_id,
        )

        await callback.answer(
            i18n["access_denied"],
            show_alert=True,
        )
        return

    bug = await complete_bug_fix(
        session,
        bug_id,
    )

    logger.info(
        "Баг #%s переведен в статус waiting_confirmation",
        bug.id,
    )

    try:
        await callback.bot.send_message(
            chat_id=bug.user_id,
            text=i18n["fix_completed_message"],
            reply_markup=get_bug_confirmation_keyboard(bug_id, i18n),
        )

        logger.info(
            "Уведомление о завершении бага #%s отправлено пользователю %s",
            bug.id,
            bug.user_id,
        )

    except Exception:
        logger.exception(
            "Не удалось отправить уведомление пользователю %s по багу #%s",
            bug.user_id,
            bug.id,
        )

    await callback.answer(
        i18n["fix_completed"]
    )