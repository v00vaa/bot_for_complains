import asyncio
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNetworkError
from config import Config, load_config
from lexicon import translations
from aiogram.fsm.storage.memory import MemoryStorage
# Импортируем роутеры
from handlers import super_admin_router, admin_router, user_router#, error_router
# Импортируем миддлвари
from middlewares import TranslatorMiddleware, DatabaseMiddleware
# Импортируем вспомогательные функции для создания нужных объектов
from services import RolesStorage
from database import create_db_session, create_tables

# Инициализируем логгер
logger = logging.getLogger(__name__)



# Функция конфигурирования и запуска бота
async def main():
    # Загружаем конфиг в переменную config
    config: Config = load_config()
    # Конфигурируем логирование
    LOG_DIR = Path("logs")
    LOG_DIR.mkdir(exist_ok=True)

    logging.basicConfig(
        level=config.log.level,
        format=config.log.format,
        handlers=[
            logging.StreamHandler(),
            RotatingFileHandler(
                LOG_DIR / "bot.log",
                maxBytes=5 * 1024 * 1024,  # 5 МБ
                backupCount=5,
                encoding="utf-8"
            )
        ]
    )
    # Выводим в консоль информацию о начале запуска бота
    logger.info('Starting bot')

    roles_storage = RolesStorage(
        super_admin=config.bot.admin_id
    )

    roles_storage.load()

    # Инициализируем объект хранилища
    storage = MemoryStorage()

    # Инициализируем бот и диспетчер
    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=storage)
    # Инициализируем другие объекты (пул соединений с БД, кеш и т.п.)
    engine, session_factory = create_db_session(config)

    await create_tables(engine)

    # Помещаем нужные объекты в workflow_data диспетчера
    dp.workflow_data.update({
        "roles": roles_storage,
        "session_factory": session_factory,
    })


    # Регистриуем роутеры
    logger.info('Подключаем роутеры')
    dp.include_router(super_admin_router)
    dp.include_router(admin_router)
    dp.include_router(user_router)
    #dp.include_router(error_router)

    # Регистрируем миддлвари
    logger.info('Подключаем миддлвари')
    dp.update.middleware(TranslatorMiddleware()) 
    dp.update.middleware(DatabaseMiddleware(session_factory))
    # Пропускаем накопившиеся апдейты и запускаем polling
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except TelegramNetworkError as e:
        logger.error("Нет соединения с Telegram: %s", e)
        return
    await dp.start_polling(bot, translations=translations)


asyncio.run(main())