"""
Роутер пользовательской части бота.

Файл содержит полный сценарий работы обычного пользователя:

1. Создание нового обращения.
2. Проверка корректности описания обращения.
3. Загрузка отчёта.
4. Просмотр собственных обращений.
5. Просмотр истории версий обращения.
6. Подтверждение или отклонение исправления.
7. Повторное открытие обращения после проверки.

Все операции с базой данных вынесены в пакет database.
Файл отвечает только за обработку Telegram-событий и связывает
между собой пользовательский интерфейс, бизнес-логику и БД.
"""
import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from services.bug_description_model import MarkovModel
from states.states import CreateBug
from keyboards import get_bug_invalid_keyboard, get_cancel_keyboard, get_user_bug_list_keyboard, get_user_keyboard, get_bug_confirmation_keyboard, get_user_bug_keyboard
from filters import TextKeyFilter
from database import close_bug, create_bug, get_bug_version_by_number, get_bug_versions_count, get_user_bug_page, get_user_bug_by_offset, get_bug_by_id, reopen_bug, update_bug, get_user_bug_page_count
from services import notify_admins_about_bug, format_user_bug_card
from services.bug_description_logger import bug_description_logger
from services.roles import RolesStorage

logger = logging.getLogger(__name__)

user_router = Router()

# Размер страницы при отображении списка обращений пользователя.
PAGE_SIZE = 5

# ------------------------------------------------------------------
# Начало работы пользователя
# ------------------------------------------------------------------
#
# После команды /start отображается главное меню пользователя.
# В отличие от администратора пользователь может:
#
# • создать новое обращение;
# • просмотреть статус своих обращений.
#
# Никаких дополнительных действий данный обработчик не выполняет.
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

# ------------------------------------------------------------------
# Создание нового обращения
# ------------------------------------------------------------------
#
# После нажатия кнопки "Пожаловаться о баге" запускается FSM.
#
# Пользователь проходит два последовательных этапа:
#
# 1. вводит описание проблемы;
# 2. прикрепляет файл отчёта.
#
# Информация временно хранится в FSM до окончания создания обращения.
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

    await state.set_state(CreateBug.waiting_description)

    await state.update_data(
        reopen=False,
    )

    await message.answer(
        i18n["enter_description"],
        reply_markup=get_cancel_keyboard(i18n),
    )

# ------------------------------------------------------------------
# Отмена создания обращения
# ------------------------------------------------------------------
#
# Позволяет прервать создание обращения на любом этапе FSM.
#
# Если пользователь повторно открывал существующее обращение,
# после отмены необходимо вернуть ему клавиатуру подтверждения,
# чтобы он мог продолжить работу позже.
@user_router.message(
    StateFilter(CreateBug),
    Command("cancel"),
)
@user_router.message(
    StateFilter(CreateBug),
    TextKeyFilter("cancel"),
)
async def process_cancel_bug_creation(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    i18n: dict[str, str],
):
    data = await state.get_data()

    bug_id = data.get("bug_id")
    reopen = data.get("reopen", False)
    invalid = data.get("invalid", False)

    await state.clear()

    await message.answer(
        i18n["creation_cancelled"],
        reply_markup=get_user_keyboard(i18n),
    )

    if reopen and bug_id:
        bug = await get_bug_by_id(session, bug_id)

        if bug:
            if invalid:
                await message.answer(
                    i18n["invalid_description_message"],
                    reply_markup=get_bug_invalid_keyboard(bug.id, i18n),
                )
            else:
                await message.answer(
                    i18n["fix_completed_message"],
                    reply_markup=get_bug_confirmation_keyboard(bug.id, i18n),
                )

# ------------------------------------------------------------------
# Проверка описания обращения
# ------------------------------------------------------------------
#
# Перед тем как разрешить загрузку файла, описание проходит
# автоматическую проверку моделью MarkovModel.
#
# Если описание признано слишком коротким или неинформативным:
#
# • пользователь получает рекомендации;
# • описание сохраняется в отдельный лог-файл;
# • переход к следующему этапу запрещается.
#
# Корректное описание сохраняется в FSM до загрузки файла.
@user_router.message(CreateBug.waiting_description)
async def process_description(
    message: Message,
    state: FSMContext,
    bug_description_model: MarkovModel,
    i18n: dict[str, str],
):
    if not bug_description_model.validate(message.text):

        bug_description_logger.info(
            message.text,
            extra={
                "user_id": message.from_user.id,
                "username": message.from_user.username or "-",
            },
        )

        await message.answer(
            i18n["bad_description"],
        )
        return

    await state.update_data(
        description=message.text,
    )

    await state.set_state(
        CreateBug.waiting_report,
    )

    await message.answer(
        i18n["attach_report"],
    )

# ------------------------------------------------------------------
# Загрузка файла отчёта
# ------------------------------------------------------------------
#
# Финальный этап создания обращения.
#
# Возможны два сценария:
#
# • создание нового обращения;
# • обновление существующего (если пользователь повторно
#   открывает обращение после отказа или повторной проверки).
#
# После успешного сохранения:
#
# • все администраторы получают уведомление;
# • FSM очищается;
# • пользователю возвращается главное меню.
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
        i18n["bug_registered"],
        reply_markup=get_user_keyboard(i18n),
    )

# Обработка любых сообщений вместо документа.
# Пользователь остаётся в том же состоянии FSM,
# пока не отправит допустимый файл.
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

# ------------------------------------------------------------------
# Подтверждение исправления
# ------------------------------------------------------------------
#
# Если пользователь подтвердил исправление,
# обращение окончательно закрывается.
#
# После этого:
#
# • клавиатура удаляется;
# • статус меняется на closed;
# • пользователь получает сообщение благодарности.
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
    bug = await close_bug(session, bug_id)

    logger.info(
            "Баг #%s переведен в статус closed",
            bug.id,
        )

    await callback.message.edit_reply_markup(
        reply_markup=None
    )
    
    await callback.answer()

    await callback.message.answer(
        i18n["thank_you"]
    )

    await callback.answer()

# ------------------------------------------------------------------
# Повторное открытие обращения
# ------------------------------------------------------------------
#
# Если пользователь считает,
# что проблема не была исправлена,
# обращение переводится в статус reopened.
#
# Затем снова запускается FSM,
# чтобы пользователь смог:
#
# • дополнить описание;
# • приложить новый отчёт.
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
    bug = await reopen_bug(session, bug_id)
    logger.info(
        "Баг #%s возвращен в статус reopened",
        bug.id,
    )
    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await callback.answer()

    await state.update_data(
        bug_id=bug.id,
        reopen=True,
    )

    await state.set_state(
        CreateBug.waiting_description
    )

    await callback.message.answer(
        i18n["enter_description"],
        reply_markup=get_cancel_keyboard(i18n),
    )

    await callback.answer()

# ------------------------------------------------------------------
# Просмотр собственных обращений
# ------------------------------------------------------------------
#
# Пользователь получает первую страницу списка своих обращений.
#
# Каждое обращение открывается отдельной кнопкой.
#
# При необходимости отображаются кнопки перехода между страницами.
@user_router.message(TextKeyFilter("status_bt"))
async def process_status(
    message: Message,
    session: AsyncSession,
    i18n: dict[str, str],
):
    bugs = await get_user_bug_page(
        session=session,
        user_id=message.from_user.id,
        page=0,
        page_size=PAGE_SIZE,
    )

    if not bugs:
        await message.answer(
            i18n["no_bugs_user"],
        )
        return

    total_pages = await get_user_bug_page_count(
        session,
        message.from_user.id,
        PAGE_SIZE,
    )

    await message.answer(
        i18n["select_bug"],
        reply_markup=get_user_bug_list_keyboard(
            bugs=bugs,
            page=0,
            has_prev=False,
            has_next=total_pages > 1,
            i18n=i18n,
        ),
    )

# ------------------------------------------------------------------
# Переход между страницами списка обращений
# ------------------------------------------------------------------
#
# Используется только кнопками пагинации.
#
# Сообщение не создаётся заново —
# изменяется существующая inline-клавиатура.
@user_router.callback_query(
    F.data.startswith("user_bug_page:")
)
async def process_user_bug_page(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: dict[str, str],
):
    page = int(callback.data.split(":")[1])

    bugs = await get_user_bug_page(
        session=session,
        user_id=callback.from_user.id,
        page=page,
        page_size=PAGE_SIZE,
    )

    total_pages = await get_user_bug_page_count(
        session,
        callback.from_user.id,
        PAGE_SIZE,
    )

    await callback.message.edit_reply_markup(
        reply_markup=get_user_bug_list_keyboard(
            bugs=bugs,
            page=page,
            has_prev=page > 0,
            has_next=page + 1 < total_pages,
            i18n=i18n,
        )
    )

    await callback.answer()

# ------------------------------------------------------------------
# Просмотр карточки обращения
# ------------------------------------------------------------------
#
# Открывает полную информацию по выбранному обращению.
#
# Дополнительно проверяется,
# что пользователь действительно является владельцем обращения.
#
# Это защищает от открытия чужих обращений
# при подмене callback_data.
@user_router.callback_query(
    F.data.startswith("user_bug_details:")
)
async def process_user_bug_details(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: dict[str, str],
):
    bug_id = int(callback.data.split(":")[1])

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

    if bug.user_id != callback.from_user.id:
        await callback.answer(
            show_alert=True,
        )
        return

    versions_count = await get_bug_versions_count(
        session,
        bug.id,
    )

    await callback.message.edit_text(
        text=format_user_bug_card(bug, i18n),
        reply_markup=get_user_bug_keyboard(
            bug_id=bug.id,
            version=bug.version,
            versions_count=versions_count,
            status=bug.status,
            i18n=i18n,
        ),
    )

    await callback.answer()

# ------------------------------------------------------------------
# Просмотр предыдущей версии обращения
# ------------------------------------------------------------------
#
# Каждое изменение обращения создаёт новую версию BugData.
#
# Пользователь может просматривать историю изменений
# с помощью кнопок навигации.
@user_router.callback_query(
    F.data.startswith("user_bug_version_prev:")
)
async def process_prev_bug_version(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: dict[str, str],
):
    _, bug_id, version = callback.data.split(":")

    bug_id = int(bug_id)
    version = int(version) - 1

    bug = await get_bug_version_by_number(
        session,
        bug_id,
        version,
    )

    versions_count = await get_bug_versions_count(
        session,
        bug_id,
    )

    await callback.message.edit_text(
        text=format_user_bug_card(
            bug,
            i18n,
        ),
        reply_markup=get_user_bug_keyboard(
            bug_id=bug_id,
            version=version,
            versions_count=versions_count,
            status=bug.status,
            i18n=i18n,
        ),
    )

    await callback.answer()

# ------------------------------------------------------------------
# Просмотр следующей версии обращения
# ------------------------------------------------------------------
#
# Работает аналогично переходу к предыдущей версии,
# но открывает более новую запись истории.
@user_router.callback_query(
    F.data.startswith("user_bug_version_next:")
)
async def process_next_bug_version(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: dict[str, str],
):
    _, bug_id, version = callback.data.split(":")

    bug_id = int(bug_id)
    version = int(version) + 1

    bug = await get_bug_version_by_number(
        session,
        bug_id,
        version,
    )

    versions_count = await get_bug_versions_count(
        session,
        bug_id,
    )

    await callback.message.edit_text(
        text=format_user_bug_card(
            bug,
            i18n,
        ),
        reply_markup=get_user_bug_keyboard(
            bug_id=bug_id,
            version=version,
            versions_count=versions_count,
            status=bug.status,
            i18n=i18n,
        ),
    )

    await callback.answer()

# ------------------------------------------------------------------
# Повторное описание некорректной заявки
# ------------------------------------------------------------------
#
# Если администратор признал описание недостаточным,
# пользователь может начать заполнение обращения заново.
#
# При этом:
#
# • сохраняется ссылка на существующее обращение;
# • запускается FSM;
# • после завершения будет создана новая версия BugData,
#   а не новое обращение.
@user_router.callback_query(
    F.data.startswith("rewrite_bug:")
)
async def process_rewrite_bug(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    i18n: dict[str, str],
):
    bug_id = int(callback.data.split(":")[1])

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

    await state.update_data(
        bug_id=bug.id,
        reopen=True,
        invalid=True,
    )

    await state.set_state(
        CreateBug.waiting_description,
    )

    await callback.message.answer(
        i18n["enter_description"],
    )

    await callback.answer()