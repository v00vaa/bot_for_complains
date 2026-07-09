"""
Клавиатуры администратора.

Файл содержит все интерфейсные элементы, с которыми работает администратор:
- главное меню;
- список обращений с пагинацией;
- карточку обращения;
- кнопку уведомления о новом обращении.

Клавиатуры не содержат бизнес-логики — они только формируют интерфейс
Telegram на основании переданных данных.
"""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

def get_admin_keyboard(i18n: dict[str, str]) -> ReplyKeyboardMarkup:
    """
    Главное меню администратора.

    Отображается после команды /start и позволяет перейти
    к просмотру списка обращений.
    """
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=i18n["bug_list"])]],
        resize_keyboard=True,
    )

def get_admin_bug_list_keyboard(
    bugs: list,
    page: int,
    has_prev: bool,
    has_next: bool,
    show_my_bugs: bool,
    i18n: dict[str, str],
) -> InlineKeyboardMarkup:
    """
    Формирует список обращений администратора.

    Содержит:
    - список обращений;
    - переключение между всеми обращениями и обращениями,
      назначенными текущему администратору;
    - кнопки пагинации.
    """
    # Кнопка для каждого обращения.
    keyboard = [
        [
            InlineKeyboardButton(
                text=f"#{bug.id} | {i18n.get(f'status_{bug.status}', bug.status)}",
                callback_data=f"bug_details:{bug.id}",
            )
        ]
        for bug in bugs
    ]

    # Кнопка переключения режима просмотра.
    keyboard.append([
        InlineKeyboardButton(
            text=(
                i18n["all_bugs"]
                if show_my_bugs
                else i18n["my_bugs"]
            ),
            callback_data=(
                f"all_bug_page:0"
                if show_my_bugs
                else f"my_bug_page:0"
            ),
        )
    ])

    navigation_row = []
    # Кнопка перехода на предыдущую страницу.
    if has_prev:
        navigation_row.append(
            InlineKeyboardButton(
                text=i18n["backward"],
                callback_data=(
                    f"{'my_bug_page' if show_my_bugs else 'all_bug_page'}:{page - 1}"
                ),
            )
        )
    # Кнопка перехода на следующую страницу.
    if has_next:
        navigation_row.append(
            InlineKeyboardButton(
                text=i18n["forward"],
                callback_data=(
                    f"{'my_bug_page' if show_my_bugs else 'all_bug_page'}:{page + 1}"
                ),
            )
        )

    if navigation_row:
        keyboard.append(navigation_row)

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )


def get_bug_card_keyboard(
    bug_id: int,
    version: int,
    oldest_version: int,
    newest_version: int,
    is_assigned_admin: bool,
    i18n: dict[str, str],
    is_training_sample: bool,
) -> InlineKeyboardMarkup:
    """
    Клавиатура карточки обращения.

    Содержимое зависит от текущего состояния обращения:

    • скачивание отчёта;
    • принятие обращения в работу;
    • пометка обращения как некорректного;
    • управление обучающей выборкой модели;
    • завершение исправления;
    • изменение критичности;
    • навигация по версиям обращения.
    """
    # Базовые действия доступны всегда.
    keyboard = [
        [InlineKeyboardButton(text=i18n["report_file"], callback_data=f"report_file:{bug_id}:{version}")],
        [InlineKeyboardButton(text=i18n["accept"], callback_data=f"accept_bug:{bug_id}")],
    ]
    # Пока обращение не принято в работу,
    # его можно отметить как некорректное.
    if not is_assigned_admin:
        keyboard.append([
            InlineKeyboardButton(
                text=i18n["invalid_description"],
                callback_data=f"invalid_bug:{bug_id}",
            )
        ])
    # Кнопка управления обучающей выборкой модели.
    if not is_training_sample:
        keyboard.append([
            InlineKeyboardButton(
                text=i18n["mark_valid"],
                callback_data=f"training_add:{bug_id}:{version}",
            )
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(
                text=i18n["mark_invalid"],
                callback_data=f"training_remove:{bug_id}:{version}",
            )
        ])
    # Завершить исправление может только назначенный администратор.
    if is_assigned_admin:
        keyboard.append([InlineKeyboardButton(text=i18n["complete_fix"], callback_data=f"complete_fix:{bug_id}")])
    keyboard.append(
    [
        InlineKeyboardButton(
            text=i18n["change_severity"],
            callback_data=f"change_severity:{bug_id}",
        )
    ]
)
    # Навигация между версиями обращения.
    navigation_row = []
    if version < newest_version:
        navigation_row.append(
            InlineKeyboardButton(text=i18n["newer_version"], callback_data=f"bug_version:{bug_id}:{version + 1}")
        )
    if version > oldest_version:
        navigation_row.append(
            InlineKeyboardButton(text=i18n["older_version"], callback_data=f"bug_version:{bug_id}:{version - 1}")
        )
    if navigation_row:
        keyboard.append(navigation_row)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_bug_notification_keyboard(
    bug_id: int,
    i18n: dict[str, str],
) -> InlineKeyboardMarkup:
    """
    Клавиатура уведомления о новом обращении.

    Используется при массовой рассылке администраторам.
    Содержит только кнопку быстрого открытия карточки обращения.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n["details"],
                    callback_data=f"bug_details:{bug_id}",
                )
            ]
        ]
    )

def get_severity_keyboard(
    bug_id: int,
    i18n: dict[str, str],
) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора критичности обращения.
    """

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n["severity_not_set"],
                    callback_data=f"set_severity:{bug_id}:not_set",
                ),
                InlineKeyboardButton(
                    text=i18n["severity_critical"],
                    callback_data=f"set_severity:{bug_id}:critical",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=i18n["severity_high"],
                    callback_data=f"set_severity:{bug_id}:high",
                ),
                InlineKeyboardButton(
                    text=i18n["severity_medium"],
                    callback_data=f"set_severity:{bug_id}:medium",
                ),
                InlineKeyboardButton(
                    text=i18n["severity_low"],
                    callback_data=f"set_severity:{bug_id}:low",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅ Назад",
                    callback_data=f"back_to_bug:{bug_id}",
                )
            ]
        ]
    )