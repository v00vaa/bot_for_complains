"""
Модуль инициализации базы данных.

Отвечает за создание подключения к СУБД и подготовку объектов
SQLAlchemy для работы приложения.

Предоставляет функции:
    • создания структуры базы данных;
    • создания асинхронного Engine;
    • создания фабрики асинхронных сессий.

Используется при запуске приложения в main.py.
"""
import logging

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine
)
from database.models import Base


from config import Config

logger = logging.getLogger(__name__)

async def create_tables(
    engine: AsyncEngine,
):
    """
    Создает все таблицы базы данных.

    SQLAlchemy анализирует зарегистрированные ORM-модели и
    создает отсутствующие таблицы. Если таблицы уже существуют,
    повторное создание не выполняется.

    Args:
        engine: Асинхронный SQLAlchemy Engine.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all
            )

        logger.info(
            "Таблицы успешно созданы"
        )

    except Exception:
        logger.exception(
            "Ошибка подключения к БД или создания таблиц"
        )
        raise


def create_db_session(config: Config):
    """
    Создает подключение к базе данных.

    Функция инициализирует:

    • асинхронный SQLAlchemy Engine;
    • фабрику асинхронных сессий (Session Factory).

    Возвращаемая фабрика используется во всех обработчиках
    Telegram-бота для получения новой сессии базы данных.

    Args:
        config: Конфигурация приложения.

    Returns:
        Кортеж (engine, session_factory).
    """
    logger.info(
        "Создание подключения к БД"
    )

    engine = create_async_engine(
        config.db.dsn,
        echo=False,
        pool_pre_ping=True,
    )

    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    logger.info(
        "Подключение к БД настроено"
    )

    return engine, session_factory