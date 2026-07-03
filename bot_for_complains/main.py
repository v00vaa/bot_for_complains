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
from services import RolesStorage, TrainingScheduler
from database import create_db_session, create_tables
from services.validator import MarkovValidator, train_validator
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

    # Инициализируем валидатор 
    validator = MarkovValidator(
        second_order_threshold=config.validator.second_order_threshold,
        first_order_threshold=config.validator.first_order_threshold,
        use_first_order=config.validator.fallback_enabled,
        bypass=config.validator.bypass,
    )
    if (
        config.validator.enabled
        and config.validator.retrain_on_start
    ):
        async with session_factory() as session:
            await train_validator(
                validator=validator,
                session=session,
                train_file=config.validator.train_file,
            )

    training_scheduler = TrainingScheduler(
        validator=validator,
        session_factory=session_factory,
        train_file=config.validator.train_file,
        threshold=config.validator.retrain_after_changes,
    )

    if config.validator.enabled and config.validator.retrain_on_start:
        logger.info("Обучение модели при запуске...")
        await training_scheduler.retrain()

    # Помещаем нужные объекты в workflow_data диспетчера
    dp.workflow_data.update({
        "roles": roles_storage,
        "session_factory": session_factory,
        "validator": validator,
        "training_scheduler": training_scheduler,
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