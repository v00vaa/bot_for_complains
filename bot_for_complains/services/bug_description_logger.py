"""
bug_description_logger.py

Настройка отдельного логгера для хранения отклонённых описаний багов.

Назначение:
    Все описания, которые модель признала недостаточно информативными,
    сохраняются в отдельный журнал.

Это позволяет:

    • анализировать ошибки пользователей;
    • улучшать обучающую выборку;
    • отслеживать работу модели;
    • проводить последующее переобучение.

Журнал не зависит от основного логирования приложения.
Он ведётся всегда независимо от уровня LOG_LEVEL.
"""
import logging
from pathlib import Path
# Каталог хранения логов
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
# Отдельный логгер только для отклонённых описаний
bug_description_logger = logging.getLogger("bug_descriptions")
# Всегда записываем информационные сообщения
bug_description_logger.setLevel(logging.INFO)
# Не передавать записи в основной логгер приложения
bug_description_logger.propagate = False

if not bug_description_logger.handlers:
     # Отдельный файл журнала
    handler = logging.FileHandler(
        LOG_DIR / "rejected_descriptions.log",
        encoding="utf-8",
    )

    handler.setLevel(logging.INFO)
    # Формат одной записи
    formatter = logging.Formatter(
        "[%(asctime)s] "
        "user=%(user_id)s "
        "username=%(username)s\n"
        "%(message)s\n"
        "------------------------------------------------------------"
    )

    handler.setFormatter(formatter)
    # Подключаем обработчик к логгеру
    bug_description_logger.addHandler(handler)
