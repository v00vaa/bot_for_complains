import logging
import os
from dataclasses import dataclass

from environs import Env

logger = logging.getLogger(__name__)


@dataclass
class BotSettings:
    token: str
    admin_id: str

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
class BugDescriptionModelConfig:
    enabled: bool
    bypass: bool
    fallback_enabled: bool

    train_file: str

    second_order_threshold: float
    first_order_threshold: float
    retrain_on_start: bool
    retrain_after_changes: int




@dataclass
class Config:
    bot: BotSettings
    db: DatabaseSettings
    #redis: RedisSettings
    log: LoggSettings
    bug_description_model: BugDescriptionModelConfig


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

    raw_id = env.str("ADMIN_ID")

    try:
        admin_id = int(raw_id)
    except ValueError as e:
        raise ValueError(f"ADMIN_ID должен быть числом, получено: {raw_id}") from e
    
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

    bug_description_model=BugDescriptionModelConfig(
        enabled=env.bool("BUG_DESCRIPTION_MODEL_ENABLED", True),
        bypass=env.bool("BUG_DESCRIPTION_MODEL_BYPASS", False),
        fallback_enabled=env.bool("BUG_DESCRIPTION_MODEL_FIRST_ORDER", True),

        train_file=env.str("BUG_DESCRIPTION_MODEL_TRAIN_FILE", r"\config\data\train.txt"),
        second_order_threshold=env.float("BUG_DESCRIPTION_MODEL_SECOND_ORDER_THRESHOLD", 0.18),

        first_order_threshold=env.float("BUG_DESCRIPTION_MODEL_FIRST_ORDER_THRESHOLD", 0.08),
        retrain_on_start=env.bool("BUG_DESCRIPTION_MODEL_RETRAIN_ON_START", True),
        retrain_after_changes=env.int("BUG_DESCRIPTION_MODEL_RETRAIN_AFTER_CHANGES", 10)
    )

    logger.info("Configuration loaded successfully")

    return Config(
        bot=BotSettings(token=token, admin_id=admin_id),
        db=db,
        #redis=redis,
        log=logg_settings,
        bug_description_model=bug_description_model
    )