from dataclasses import dataclass
from environs import Env


@dataclass
class DatabaseConfig:
    name: str         # Название базы данных
    host: str         # URL-адрес базы данных
    user: str         # Username пользователя базы данных
    password: str     # Пароль к базе данных


@dataclass
class TgBot:
    token: str            # Токен для доступа к телеграм-боту
    admin_ids: list[int]  # Список id администраторов бота


@dataclass
class Config:
    bot: TgBot
    db: DatabaseConfig


# Создаем экземпляр класса Env
env: Env = Env()

# Добавляем в переменные окружения данные, прочитанные из файла .env 
env.read_env()

# Создаем экземпляр класса Config и наполняем его данными из переменных окружения
config = Config(
    bot=TgBot(
        token=env('BOT_TOKEN'),
        admin_ids=list(map(int, env.list('ADMIN_IDS')))
    ),
    db=DatabaseConfig(
        name=env('DB_NAME'),
        host=env('DB_HOST'),
        user=env('DB_USER'),
        password=env('DB_PASSWORD')
    )
)

# Выводим значения полей экземпляра класса Config на печать, 
# чтобы убедиться, что все данные, получаемые из переменных окружения, доступны
print('BOT_TOKEN:', config.bot.token)
print('ADMIN_IDS:', config.bot.admin_ids)
print()
print('DB_NAME:', config.db.name)
print('DB_HOST:', config.db.host)
print('DB_USER:', config.db.user)
print('DB_PASSWORD:', config.db.password)