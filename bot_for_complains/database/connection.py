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