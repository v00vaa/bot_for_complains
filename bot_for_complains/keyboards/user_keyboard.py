"""
Клавиатуры пользовательской части бота.

Файл содержит все ReplyKeyboard и InlineKeyboard, с которыми
взаимодействует обычный пользователь:

- главное меню;
- подтверждение исправления бага;
- просмотр списка обращений;
- просмотр истории версий;
- отмена текущего действия;
- запрос на повторное описание бага.

Все тексты кнопок берутся из словаря локализации (i18n)
"""
from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

def get_user_keyboard(i18n: dict[str, str]) -> ReplyKeyboardMarkup:
    """
    Создает главное меню пользователя.

    Содержит две основные команды:
        • создание нового обращения;
        • просмотр статуса существующих обращений.

    Используется после команды /start и после завершения любых сценариев.
    """
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
    """
    Клавиатура подтверждения исправления бага.

    Показывается пользователю после того, как администратор отметил
    обращение как исправленное.

    Кнопки:
        • Подтверждаю — баг действительно исправлен.
        • Не подтверждаю — проблема сохранилась.
    """
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
    version: int,
    versions_count: int,
    status: str,
    i18n: dict[str, str],
) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру карточки обращения пользователя.

    Возможности:
        • переход между версиями обращения;
        • подтверждение исправления (если обращение ожидает проверки).

    Кнопки подтверждения отображаются только при статусе
    waiting_confirmation.
    """
    keyboard = []

    navigation = []

    # Кнопка перехода к предыдущей версии обращения.
    if version > 1:
        navigation.append(
            InlineKeyboardButton(
                text=i18n["backward"],
                callback_data=f"user_bug_version_prev:{bug_id}:{version}",
            )
        )
        # Кнопка перехода к следующей версии обращения.
    if version < versions_count:
        navigation.append(
            InlineKeyboardButton(
                text=i18n["forward"],
                callback_data=f"user_bug_version_next:{bug_id}:{version}",
            )
        )
    # Добавляем навигацию только если существует хотя бы одна соседняя версия.
    if navigation:
        keyboard.append(navigation)

    # После завершения исправления пользователь может подтвердить
    # или отклонить результат работы администратора.
    if status == "waiting_confirmation":
        keyboard.extend(
            [
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
                ],
            ]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard,
    )

def get_user_bug_list_keyboard(
    bugs: list,
    page: int,
    has_prev: bool,
    has_next: bool,
    i18n: dict[str, str],
) -> InlineKeyboardMarkup:
    """
    Формирует список обращений пользователя.

    Каждая строка содержит:
        • номер обращения;
        • текущий статус.

    Внизу автоматически добавляются кнопки постраничной навигации.
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text=f"#{bug.id} | {i18n.get(f'status_{bug.status}', bug.status)}",
                callback_data=f"user_bug_details:{bug.id}",
            )
        ]
        for bug in bugs
    ]

    navigation = []
    # Переход на предыдущую страницу.
    if has_prev:
        navigation.append(
            InlineKeyboardButton(
                text=i18n["backward"],
                callback_data=f"user_bug_page:{page-1}",
            )
        )
    # Переход на следующую страницу.
    if has_next:
        navigation.append(
            InlineKeyboardButton(
                text=i18n["forward"],
                callback_data=f"user_bug_page:{page+1}",
            )
        )

    if navigation:
        keyboard.append(navigation)

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )

def get_cancel_keyboard(
    i18n: dict[str, str],
) -> ReplyKeyboardMarkup:
    """
    Клавиатура с единственной кнопкой отмены.

    Используется во всех пошаговых сценариях FSM
    (создание обращения, повторное описание и т.д.).
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=i18n["cancel"],
                )
            ]
        ],
        resize_keyboard=True,
    )

def get_bug_invalid_keyboard(
    bug_id: int,
    i18n: dict[str, str],
) -> ReplyKeyboardMarkup:
    """
    Клавиатура повторного заполнения описания.

    Показывается пользователю, если администратор признал описание
    недостаточно информативным.

    После нажатия запускается сценарий повторного редактирования
    текущего обращения.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n["rewrite_description"],
                    callback_data=f"rewrite_bug:{bug_id}",
                )
            ]
        ]
    )