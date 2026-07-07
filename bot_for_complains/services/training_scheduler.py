"""
training_scheduler.py

Сервис автоматического переобучения модели проверки описаний багов.

Назначение:
    При добавлении или удалении примеров из обучающей выборки модель не
    переобучается сразу после каждого изменения. Вместо этого используется
    счётчик изменений.

    После достижения заданного порога автоматически запускается обучение
    модели в отдельной асинхронной задаче.

Преимущества:
    • уменьшается нагрузка на сервер;
    • исключается многократное переобучение подряд;
    • одновременно может выполняться только одно обучение.
"""
import asyncio
import logging

from services.bug_description_model import train_bug_description_model

logger = logging.getLogger(__name__)


class TrainingScheduler:
    """
    Управляет автоматическим переобучением модели.

    Объект хранится один на всё приложение и получает уведомления
    каждый раз, когда администратор изменяет обучающую выборку.
    """
    def __init__(
        self,
        bug_description_model,
        session_factory,
        train_file: str,
        threshold: int,
    ):
        # Экземпляр модели проверки описаний
        self.bug_description_model = bug_description_model
        # Фабрика создания SQLAlchemy-сессий
        self.session_factory = session_factory
        # Файл с базовыми тренировочными примерами
        self.train_file = train_file
        # Количество изменений, после которого запускается обучение
        self.threshold = threshold
        # Текущее количество изменений
        self.counter = 0
        # Защита от одновременного запуска нескольких обучений
        self._lock = asyncio.Lock()
        # Флаг выполняющегося обучения
        self._training = False

    async def retrain(self):
        """
        Выполняет полное переобучение модели.

        Если обучение уже выполняется, повторный запуск невозможен.
        """
        async with self._lock:
            if self._training:
                return

            self._training = True

        try:
            logger.info("Начато обучение модели проверки описаний")

            async with self.session_factory() as session:
                await train_bug_description_model(
                    self.bug_description_model,
                    session,
                    self.train_file,
                )

            logger.info("Обучение модели успешно завершено")

        except Exception:
            logger.exception("Ошибка во время обучения модели")

        finally:
            async with self._lock:
                self._training = False

    async def notify_change(self):
        """
        Вызывается после изменения обучающей выборки.

        Увеличивает внутренний счётчик.
        После достижения порога автоматически запускает обучение.
        """
        async with self._lock:
            self.counter += 1

            if self.counter < self.threshold:
                return
            # Начат новый цикл подсчёта
            self.counter = 0

            if self._training:
                return
        # Запуск обучения в фоне, не блокируя обработку Telegram
        asyncio.create_task(self.retrain())