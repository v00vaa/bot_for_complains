import logging
import os
from dataclasses import dataclass

from environs import Env

logger = logging.getLogger(__name__)


@dataclass
class BotSettings:
    token: str
    admin_id: int

@dataclass
class DatabaseSettings:
    name: str
    host: str
    port: int
    user: str
    password: str

    @property
    def dsn(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )

#@dataclass
#class RedisSettings:
#    host: str
#    port: int
#    db: int
#    password: str
#    username: str


@dataclass
class LoggSettings:
    level: str
    format: str


@dataclass
class Config:
    bot: BotSettings
    db: DatabaseSettings
    #redis: RedisSettings
    log: LoggSettings


def load_config(path: str | None = None) -> Config:
    env = Env()

    if path:
        if not os.path.exists(path):
            logger.warning(".env file not found at '%s', skipping...", path)
        else:
            logger.info("Loading .env from '%s'", path)

    env.read_env(path)

    token = env("BOT_TOKEN")

    if not token:
        raise ValueError("BOT_TOKEN must not be empty")

    raw_ids = env.int("ADMIN_IDS")

    try:
        admin_id = raw_ids
    except ValueError as e:
        raise ValueError(f"ADMIN_IDS must be integers, got: {raw_ids}") from e
    
    db = DatabaseSettings(
        name=env("POSTGRES_DB"),
        host=env("POSTGRES_HOST"),
        port=env.int("POSTGRES_PORT"),
        user=env("POSTGRES_USER"),
        password=env("POSTGRES_PASSWORD"),
    )

    #redis = RedisSettings(
    #    host=env("REDIS_HOST"),
    #    port=env.int("REDIS_PORT"),
    #    db=env.int("REDIS_DATABASE"),
    #    password=env("REDIS_PASSWORD", default=""),
    #    username=env("REDIS_USERNAME", default=""),
    #)

    logg_settings = LoggSettings(
        level=env("LOG_LEVEL"),
        format=env("LOG_FORMAT")
    )

    logger.info("Configuration loaded successfully")

    return Config(
        bot=BotSettings(token=token, admin_id=admin_id),
        db=db,
        #redis=redis,
        log=logg_settings
    )