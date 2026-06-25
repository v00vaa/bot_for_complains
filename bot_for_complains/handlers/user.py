import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from states.states import CreateBug
from keyboards import get_user_keyboard, get_bug_confirmation_keyboard, get_bug_details_keyboard, get_user_bug_keyboard
from filters import TextKeyFilter
from database import create_bug, get_user_bugs_count, get_user_bug_by_offset, get_bug_by_id, update_bug
from services import notify_admins_about_bug, format_user_bug_card
from services.roles import RolesStorage

logger = logging.getLogger(__name__)

user_router = Router()


@user_router.message(CommandStart())
async def process_start_command(
    message: Message,
    i18n: dict[str, str]
):
    logger.info(
        "Пользователь %s выполнил /start",
        message.from_user.id,
    )

    await message.answer(
        text=i18n["/start_user"],
        reply_markup=get_user_keyboard(i18n)
    )


@user_router.message(TextKeyFilter("report_bt"))
async def process_report_bug(
    message: Message,
    state: FSMContext,
    i18n: dict[str, str]
):
    logger.info(
        "Пользователь %s начал создание заявки",
        message.from_user.id,
    )

    await state.set_state(
        CreateBug.waiting_description
    )

    await message.answer(
        i18n["enter_description"]
    )


@user_router.message(CreateBug.waiting_description)
async def process_description(
    message: Message,
    state: FSMContext,
    i18n: dict[str, str]
):
    logger.info(
        "Пользователь %s отправил описание проблемы",
        message.from_user.id,
    )

    await state.update_data(
        description=message.text
    )

    await state.set_state(
        CreateBug.waiting_report
    )

    await message.answer(
        i18n["attach_report"]
    )


@user_router.message(
    CreateBug.waiting_report,
    F.document
)
async def process_report_file(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    roles: RolesStorage,
    i18n: dict[str, str]
):
    document = message.document

    if not document.file_name.lower().endswith(
        (".docx", ".txt")
    ):
        logger.warning(
            "Пользователь %s отправил файл неподдерживаемого типа: %s",
            message.from_user.id,
            document.file_name,
        )

        await message.answer(
            i18n["wrong_file_type"]
        )
        return

    data = await state.get_data()

    description = data["description"]

    bug_id = data.get("bug_id")

    if bug_id:
        bug = await update_bug(
            session=session,
            bug_id=bug_id,
            description=data["description"],
            file_id=document.file_id,
            file_name=document.file_name,
        )

        logger.info(
            "Баг #%s был повторно открыт пользователем %s",
            bug.id,
            message.from_user.id,
        )
    else:
        bug = await create_bug(
            session=session,
            user_id=message.from_user.id,
            description=data["description"],
            file_id=document.file_id,
            file_name=document.file_name,
        )

        logger.info(
            "Создан новый баг #%s пользователем %s",
            bug.id,
            message.from_user.id,
        )

    await notify_admins_about_bug(
        bot=message.bot,
        admin_ids=roles.get_admins(),
        bug_id=bug.id,
        i18n=i18n,
    )

    logger.info(
        "Администраторы уведомлены о баге #%s",
        bug.id,
    )

    await state.clear()

    await message.answer(
        i18n["bug_registered"]
    )


@user_router.message(
    CreateBug.waiting_report
)
async def process_wrong_file(
    message: Message,
    i18n: dict[str, str]
):
    await message.answer(
        i18n["send_valid_file"]
    )


@user_router.message(
    TextKeyFilter("status_bt")
)
async def process_status(
    message: Message,
    session: AsyncSession,
    i18n: dict[str, str],
):
    logger.info(
        "Пользователь %s запросил список своих багов",
        message.from_user.id,
    )

    bug = await get_user_bug_by_offset(
        session=session,
        user_id=message.from_user.id,
        offset=0,
    )

    if bug is None:
        await message.answer(
            i18n["no_bugs_user"]
        )
        return

    total = await get_user_bugs_count(
        session,
        message.from_user.id,
    )

    await message.answer(
    text=format_user_bug_card(bug, i18n),
    reply_markup=get_user_bug_keyboard(
        bug_id=bug.id,
        status=bug.status,
        index=0,
        has_prev=False,
        has_next=total > 1,
        i18n=i18n,
    )
)

@user_router.callback_query(
    F.data.startswith("user_bug_next:")
)
async def process_next_user_bug(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: dict[str, str],
):
    current_index = int(
        callback.data.split(":")[1]
    )

    next_index = current_index + 1

    bug = await get_user_bug_by_offset(
        session=session,
        user_id=callback.from_user.id,
        offset=next_index,
    )

    if bug is None:
        await callback.answer()
        return

    total = await get_user_bugs_count(
        session,
        callback.from_user.id,
    )

    await callback.message.edit_text(
        text=format_user_bug_card(bug, i18n),
        reply_markup=get_user_bug_keyboard(
            bug_id=bug.id,
            status=bug.status,
            index=next_index,
            has_prev=next_index > 0,
            has_next=next_index < total - 1,
            i18n=i18n,
        )
    )

    await callback.answer()

@user_router.callback_query(
    F.data.startswith("user_bug_prev:")
)
async def process_prev_user_bug(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: dict[str, str],
):
    current_index = int(
        callback.data.split(":")[1]
    )

    prev_index = current_index - 1

    if prev_index < 0:
        await callback.answer()
        return

    bug = await get_user_bug_by_offset(
        session=session,
        user_id=callback.from_user.id,
        offset=prev_index,
    )

    total = await get_user_bugs_count(
        session,
        callback.from_user.id,
    )

    await callback.message.edit_text(
        text=format_user_bug_card(bug, i18n),
        reply_markup=get_user_bug_keyboard(
            bug_id=bug.id,
            status=bug.status,
            index=prev_index,
            has_prev=prev_index > 0,
            has_next=prev_index < total - 1,
            i18n=i18n,
        )
    )

    await callback.answer()

@user_router.callback_query(
    F.data.startswith("bug_confirm:")
)
async def process_bug_confirm(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: dict[str, str],
):

    bug_id = int(
        callback.data.split(":")[1]
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
    logger.info(
        "Пользователь %s подтвердил исправление бага #%s",
        callback.from_user.id,
        bug.id,
    )
    bug.status = "closed"

    logger.info(
            "Баг #%s переведен в статус closed",
            bug.id,
        )

    await callback.message.edit_reply_markup(
        reply_markup=None
    )
    
    await callback.answer()

    await session.commit()

    await callback.message.answer(
        i18n["thank_you"]
    )

    await callback.answer()

@user_router.callback_query(
    F.data.startswith("bug_reject:")
)
async def process_bug_reject(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    i18n: dict[str, str],
):
    bug_id = int(
        callback.data.split(":")[1]
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
    logger.info(
        "Пользователь %s отклонил исправление бага #%s",
        callback.from_user.id,
        bug.id,
    )
    bug.status = "reopened"
    bug.assigned_admin_id = None
    bug.assigned_admin_username = None
    await session.commit()
    logger.info(
        "Баг #%s возвращен в статус reopened",
        bug.id,
    )
    await session.commit()

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await callback.answer()

    await state.update_data(
        bug_id=bug.id,
    )

    await state.set_state(
        CreateBug.waiting_description
    )

    await callback.message.answer(
        i18n["enter_description"]
    )

    await callback.answer()