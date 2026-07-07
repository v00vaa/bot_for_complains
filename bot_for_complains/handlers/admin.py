import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import Config
from database import (
    BugView,
    accept_bug,
    complete_bug_fix,
    get_admin_bugs_count,
    get_admin_bugs_page,
    get_bug_by_id,
    get_bug_page,   
    get_bug_page_count,
    get_bug_version_by_number,
    get_bug_versions_count,  
    get_bugs_count,  
    get_bugs_page,  
    invalidate_bug,      
    set_bug_severity,           
    set_training_sample,  
)
from filters import IsAdmin, TextKeyFilter
from keyboards import (
    get_admin_bug_list_keyboard,
    get_admin_keyboard,
    get_bug_card_keyboard,
    get_bug_confirmation_keyboard,
)
from services import TrainingScheduler, format_bug_card
from services.bug_description_model import MarkovModel

logger = logging.getLogger(__name__)

admin_router = Router()

# Количество багов, отображаемых на одной странице списка.
PAGE_SIZE = 5


def _is_assigned_admin(bug, admin_id: int) -> bool:
    """
    Проверяет, назначено ли обращение текущему администратору.

    Используется для отображения различных кнопок
    (например, "Завершить исправление")
    только ответственному исполнителю.
    """
    return bug.status == "in_progress" and bug.assigned_admin_id == admin_id

async def _get_bug_keyboard(
    session: AsyncSession,
    bug: BugView,
    admin_id: int,
    i18n: dict[str, str],
):
    """
    Формирует клавиатуру карточки обращения.

    Перед созданием клавиатуры определяется:
        • количество версий обращения;
        • назначен ли текущий администратор исполнителем;
        • входит ли версия в обучающую выборку.

    Эти данные влияют на отображаемые кнопки.
    """
    newest_version = await get_bug_versions_count(session, bug.id)
    return get_bug_card_keyboard(
        bug_id=bug.id,
        version=bug.version,
        oldest_version=1,
        newest_version=newest_version,
        is_assigned_admin=_is_assigned_admin(bug, admin_id),
        i18n=i18n,
        is_training_sample=bug.is_training_sample
    )

# Запуск для администратора
@admin_router.message(CommandStart(), IsAdmin())
async def process_start_command(message: Message, i18n: dict[str, str]):
    logger.info("Администратор %s запустил бота", message.from_user.id)
    await message.answer(
        text=i18n["/start_admin"],
        reply_markup=get_admin_keyboard(i18n),
    )

# --------------------------------------------------------------------------
# Список всех обращений.
#
# Пользователю отображается только первая страница.
# Дальнейшая навигация выполняется callback-кнопками.
#
# Используется серверная пагинация, поэтому из базы извлекается
# только PAGE_SIZE записей.
# --------------------------------------------------------------------------
@admin_router.message(
    TextKeyFilter("bug_list")
)
async def process_bug_list(
    message: Message,
    session: AsyncSession,
    i18n: dict[str, str],
):
    bugs = await get_bug_page(
        session=session,
        page=0,
        page_size=PAGE_SIZE,
    )

    if not bugs:
        await message.answer(
            i18n["no_bugs_admin"],
        )
        return

    total_pages = await get_bug_page_count(
        session,
        PAGE_SIZE,
    )

    await message.answer(
        i18n["select_bug"],
        reply_markup=get_admin_bug_list_keyboard(
            bugs=bugs,
            page=0,
            has_prev=False,
            has_next=total_pages > 1,
            show_my_bugs=False,
            i18n=i18n,
        ),
    )

# Просмотр списка всех багов 
@admin_router.callback_query(
    F.data.startswith("all_bug_page:")
)
async def process_all_bug_page(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: dict[str, str],
):
    page = int(callback.data.split(":")[1])

    bugs = await get_bugs_page(
        session=session,
        page=page,
        limit=PAGE_SIZE,
    )

    total = await get_bugs_count(session)

    await callback.message.edit_reply_markup(
        reply_markup=get_admin_bug_list_keyboard(
            bugs=bugs,
            page=page,
            has_prev=page > 0,
            has_next=(page + 1) * PAGE_SIZE < total,
            show_my_bugs=False,
            i18n=i18n,
        )
    )

    await callback.answer()

# Просмотр списка багов, над которыми работает админ
@admin_router.callback_query(
    F.data.startswith("my_bug_page:")
)
async def process_my_bug_page(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: dict[str, str],
):
    page = int(callback.data.split(":")[1])

    bugs = await get_admin_bugs_page(
        session=session,
        admin_id=callback.from_user.id,
        page=page,
        limit=PAGE_SIZE,
    )

    total = await get_admin_bugs_count(
        session=session,
        admin_id=callback.from_user.id,
    )

    if not bugs:
        await callback.answer(
            i18n["no_my_bugs"],
            show_alert=True,
        )
        return

    await callback.message.edit_reply_markup(
        reply_markup=get_admin_bug_list_keyboard(
            bugs=bugs,
            page=page,
            has_prev=page > 0,
            has_next=(page + 1) * PAGE_SIZE < total,
            show_my_bugs=True,
            i18n=i18n,
        )
    )

    await callback.answer()

# --------------------------------------------------------------------------
# Открытие карточки обращения.
#
# После выбора обращения администратор получает подробную информацию:
#
#     • описание;
#     • статус;
#     • критичность;
#     • автора;
#     • историю изменений;
#     • кнопки управления.
#
# Карточка всегда показывает последнюю версию обращения.
# Старые версии открываются отдельными callback.
# --------------------------------------------------------------------------
@admin_router.callback_query(F.data.startswith("bug_details:"), IsAdmin())
async def process_bug_details(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: dict[str, str],
):
    bug_id = int(callback.data.split(":")[1])
    bug = await get_bug_by_id(session, bug_id)

    if bug is None:
        await callback.answer(i18n["bug_not_found"], show_alert=True)
        return

    logger.info(
        "Администратор %s открыл обращение #%s",
        callback.from_user.id,
        bug_id,
    )
    await callback.message.answer(
        text=format_bug_card(bug, i18n),
        reply_markup=await _get_bug_keyboard(session, bug, callback.from_user.id, i18n),
    )
    await callback.answer()

# --------------------------------------------------------------------------
# Открытие карточки обращения по введенному номеру.
#
# Используется как быстрый способ перехода к обращению
# без поиска по спискам.
# --------------------------------------------------------------------------
@admin_router.message(F.text.regexp(r"^\d+$"), IsAdmin())
async def process_bug_by_id(
    message: Message,
    session: AsyncSession,
    i18n: dict[str, str],
):
    bug_id = int(message.text)
    bug = await get_bug_by_id(session, bug_id)

    if bug is None:
        await message.answer(i18n["bug_not_found"])
        return

    logger.info("Администратор %s открыл обращение #%s по id", message.from_user.id, bug_id)
    await message.answer(
        text=format_bug_card(bug, i18n),
        reply_markup=await _get_bug_keyboard(session, bug, message.from_user.id, i18n),
    )

# --------------------------------------------------------------------------
# Изменение критичности обращения.
#
# Критичность хранится в истории статусов.
# Поэтому изменение не редактирует существующую запись,
# а создает новый BugStatus с обновленным severity.
# --------------------------------------------------------------------------
@admin_router.callback_query(F.data.startswith("set_severity:"), IsAdmin())
async def process_set_severity(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: dict[str, str],
):
    _, bug_id, severity = callback.data.split(":")
    bug = await set_bug_severity(session, int(bug_id), severity)

    if bug is None:
        await callback.answer(i18n["bug_not_found"], show_alert=True)
        return

    logger.info(
        "Администратор %s установил критичность '%s' для обращения #%s",
        callback.from_user.id,
        severity,
        bug_id,
    )
    await callback.message.edit_text(
        text=format_bug_card(bug, i18n),
        reply_markup=await _get_bug_keyboard(session, bug, callback.from_user.id, i18n),
    )
    await callback.answer(i18n["severity_updated"])

# --------------------------------------------------------------------------
# Просмотр конкретной версии обращения.
#
# Каждое повторное открытие обращения создает новую запись BugData.
# Благодаря этому сохраняется полная история изменений.
#
# Навигация осуществляется кнопками "Старее" и "Новее".
#
# Важно:
#     версии являются неизменяемыми.
#     Администратор никогда не редактирует старые записи.
# --------------------------------------------------------------------------
@admin_router.callback_query(F.data.startswith("bug_version:"), IsAdmin())
async def process_bug_version(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: dict[str, str],
):
    _, bug_id, version = callback.data.split(":")
    bug = await get_bug_version_by_number(session, int(bug_id), int(version))

    if bug is None:
        await callback.answer(i18n["bug_not_found"], show_alert=True)
        return

    logger.info(
        "Администратор %s открыл обращение #%s версия %s",
        callback.from_user.id,
        bug_id,
        version,
    )
    await callback.message.edit_text(
        text=format_bug_card(bug, i18n),
        reply_markup=await _get_bug_keyboard(session, bug, callback.from_user.id, i18n),
    )
    await callback.answer()

# --------------------------------------------------------------------------
# Отправка администратору файла отчета.
#
# Можно открыть как файл текущей версии,
# так и файл любой предыдущей версии обращения.
# --------------------------------------------------------------------------
@admin_router.callback_query(F.data.startswith("report_file:"), IsAdmin())
async def process_report_file(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: dict[str, str],
):
    parts = callback.data.split(":")
    bug_id = int(parts[1])
    version = int(parts[2]) if len(parts) > 2 else None
    bug = (
        await get_bug_version_by_number(session, bug_id, version)
        if version
        else await get_bug_by_id(session, bug_id)
    )

    if bug is None:
        await callback.answer(i18n["bug_not_found"], show_alert=True)
        return

    logger.info(
        "Администратор %s requested file for bug #%s version %s",
        callback.from_user.id,
        bug_id,
        bug.version,
    )
    await callback.bot.send_document(
        chat_id=callback.from_user.id,
        document=bug.report_file_id,
    )
    await callback.answer()

# --------------------------------------------------------------------------
# Назначение обращения администратору.
#
# После принятия:
#
#     статус -> in_progress
#
# сохраняется идентификатор администратора,
# который теперь отвечает за данное обращение.
# --------------------------------------------------------------------------
@admin_router.callback_query(F.data.startswith("accept_bug:"), IsAdmin())
async def process_accept_bug(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: dict[str, str],
):
    bug_id = int(callback.data.split(":")[1])
    bug = await accept_bug(
        session=session,
        bug_id=bug_id,
        admin_id=callback.from_user.id,
        admin_username=callback.from_user.username,
    )
    # После принятия обращения администратор становится
    # ответственным исполнителем.
    if bug is None:
        await callback.answer(i18n["bug_not_found"], show_alert=True)
        return

    logger.info("Администратор %s принял обращение #%s", callback.from_user.id, bug_id)
    await callback.message.edit_text(
        text=format_bug_card(bug, i18n),
        reply_markup=await _get_bug_keyboard(session, bug, callback.from_user.id, i18n),
    )
    await callback.answer(i18n["bug_accepted"])

# --------------------------------------------------------------------------
# Завершение исправления.
#
# После завершения:
#
#     статус -> waiting_confirmation
#
# Пользователю автоматически отправляется сообщение
# с просьбой проверить исправление.
#
# Далее возможны два сценария:
#
#     Подтверждение
#         -> обращение закрывается.
#
#     Отказ
#         -> создается новая версия обращения,
#            процесс начинается заново.
# --------------------------------------------------------------------------
@admin_router.callback_query(F.data.startswith("complete_fix:"), IsAdmin())
async def process_complete_fix(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: dict[str, str],
):
    bug_id = int(callback.data.split(":")[1])
    bug = await get_bug_by_id(session, bug_id)

    if bug is None:
        await callback.answer(i18n["bug_not_found"], show_alert=True)
        return
    # Завершить исправление может только тот администратор,
    # которому назначено обращение.
    if bug.assigned_admin_id != callback.from_user.id:
        await callback.answer(i18n["access_denied"], show_alert=True)
        return

    bug = await complete_bug_fix(session, bug_id)
    logger.info("Администратор %s завершил обращение #%s", callback.from_user.id, bug_id)

    await callback.bot.send_message(
        chat_id=bug.user_id,
        text=i18n["fix_completed_message"],
        reply_markup=get_bug_confirmation_keyboard(bug_id, i18n),
    )
    await callback.message.edit_text(
        text=format_bug_card(bug, i18n),
        reply_markup=await _get_bug_keyboard(session, bug, callback.from_user.id, i18n),
    )
    await callback.answer(i18n["fix_completed"])


# --------------------------------------------------------------------------
# Пометка обращения как содержащего недостаточное описание.
#
# Используется в случаях, когда автоматическая модель пропустила
# слишком короткое или бессодержательное описание.
#
# После нажатия кнопки:
#
#     статус -> invalid_description
#
# Пользователь получает уведомление
# с просьбой заново оформить обращение.
#
# Это позволяет не засорять очередь разработчиков
# неполными сообщениями.
# --------------------------------------------------------------------------
@admin_router.callback_query(
    F.data.startswith("invalid_bug:"),
    IsAdmin(),
)
async def process_invalid_bug(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: dict[str, str],
):
    bug_id = int(callback.data.split(":")[1])

    bug = await invalidate_bug(
        session,
        bug_id,
    )

    if bug is None:
        await callback.answer(
            i18n["bug_not_found"],
            show_alert=True,
        )
        return
    # Пользователь получает предложение заново описать проблему.
    # После этого будет создана новая версия обращения.
    await callback.bot.send_message(
        chat_id=bug.user_id,
        text=i18n["invalid_description_message"],
        reply_markup=get_bug_confirmation_keyboard(
            bug.id,
            i18n,
        ),
    )

    await callback.message.edit_text(
        format_bug_card(
            bug,
            i18n,
        ),
        reply_markup=await _get_bug_keyboard(
            session,
            bug,
            callback.from_user.id,
            i18n,
        ),
    )

    await callback.answer()

# --------------------------------------------------------------------------
# Добавление обращения в обучающую выборку.
#
# Данная функция не влияет на работу пользователя.
#
# Она используется исключительно администраторами
# для постепенного накопления качественного корпуса.
#
# После нажатия:
#
#     is_training_sample = True
#
# TrainingScheduler увеличивает счетчик изменений.
#
# Когда накопится достаточное количество изменений,
# модель автоматически переобучится.
#
# для обучения модели команда человека не требуется
# --------------------------------------------------------------------------
@admin_router.callback_query(
    F.data.startswith("training_add:")
)
async def process_training_add(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: dict[str, str],
    training_scheduler: TrainingScheduler,
):
    _, bug_id, version = callback.data.split(":")

    bug = await get_bug_version_by_number(
        session,
        int(bug_id),
        int(version),
    )

    if bug is None:
        await callback.answer(
            i18n["bug_not_found"],
            show_alert=True,
        )
        return

    changed = await set_training_sample(
        session,
        bug.bug_data_id,
        True,
    )

    if changed:
        # После изменения обучающей выборки уведомляем планировщик.
        # Если накоплено достаточное количество изменений,
        # модель будет переобучена автоматически.
        await training_scheduler.notify_change()
        bug = await get_bug_version_by_number(
            session,
            int(bug_id),
            int(version),
        )

    await callback.message.edit_reply_markup(
        reply_markup=await _get_bug_keyboard(
            session,
            bug,
            callback.from_user.id,
            i18n,
        ),
    )

    await callback.answer(
        i18n["added_to_training"],
    )

# --------------------------------------------------------------------------
# Исключение обращения из обучающей выборки.
#
# Используется если администратор ошибочно добавил запись
# либо понял, что описание является некачественным.
#
# После удаления также увеличивается счетчик изменений,
# поскольку обучающий корпус изменился.
#
# При достижении порога выполняется автоматическое
# переобучение модели.
# --------------------------------------------------------------------------
@admin_router.callback_query(
    F.data.startswith("training_remove:")
)
async def process_training_remove(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: dict[str, str],
    training_scheduler: TrainingScheduler,
):
    _, bug_id, version = callback.data.split(":")

    bug = await get_bug_version_by_number(
        session,
        int(bug_id),
        int(version),
    )

    if bug is None:
        await callback.answer(
            i18n["bug_not_found"],
            show_alert=True,
        )
        return

    changed = await set_training_sample(
        session,
        bug.bug_data_id,
        False,
    )

    if changed:
        # После изменения обучающей выборки уведомляем планировщик.
        # Если накоплено достаточное количество изменений,
        # модель будет переобучена автоматически.
        await training_scheduler.notify_change()

        bug = await get_bug_version_by_number(
            session,
            int(bug_id),
            int(version),
        )

    await callback.message.edit_reply_markup(
        reply_markup=await _get_bug_keyboard(
            session,
            bug,
            callback.from_user.id,
            i18n,
        ),
    )

    await callback.answer(
        i18n["removed_from_training"],
    )