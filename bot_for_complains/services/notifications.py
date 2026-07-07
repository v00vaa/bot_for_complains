"""
notifications.py

Отправка уведомлений администраторам о новых обращениях пользователей.

Каждый администратор получает сообщение с кнопкой быстрого перехода
к карточке нового бага.

Небольшая задержка между сообщениями позволяет избежать превышения
лимитов Telegram Bot API.
"""
import asyncio
import logging

from aiogram import Bot

from keyboards.admin_keyboard import get_bug_notification_keyboard


logger = logging.getLogger(__name__)


async def notify_admins_about_bug(
    bot: Bot,
    admin_ids: set[int],
    bug_id: int,
    i18n: dict[str, str],
) -> None:
    """
    Рассылает уведомление всем администраторам.

    Args:
        bot:
            Экземпляр Telegram-бота.

        admin_ids:
            Список Telegram ID администраторов.

        bug_id:
            Идентификатор созданного обращения.

        i18n:
            Словарь локализованных сообщений.
    """

    for admin_id in admin_ids:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=i18n["new_bug"],
                reply_markup=get_bug_notification_keyboard(
                    bug_id,
                    i18n,
                ),
            )

            # Небольшая задержка между сообщениями
            # уменьшает вероятность получения FloodWait.
            await asyncio.sleep(0.05)

        except Exception as error:
            logger.exception(
                "Не удалось уведомить администратора %s",
                admin_id,
                exc_info=error,
            )
