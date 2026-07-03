import asyncio
import logging

from services.validator import train_validator

logger = logging.getLogger(__name__)


class TrainingScheduler:
    def __init__(
        self,
        validator,
        session_factory,
        train_file: str,
        threshold: int,
    ):
        self.validator = validator
        self.session_factory = session_factory
        self.train_file = train_file

        self.threshold = threshold
        self.counter = 0

        self._lock = asyncio.Lock()
        self._training = False

    async def retrain(self):
        async with self._lock:
            if self._training:
                return

            self._training = True

        try:
            logger.info("Начато обучение валидатора")

            async with self.session_factory() as session:
                await train_validator(
                    self.validator,
                    session,
                    self.train_file,
                )

            logger.info("Обучение валидатора завершено")

        except Exception:
            logger.exception("Ошибка обучения валидатора")

        finally:
            async with self._lock:
                self._training = False

    async def notify_change(self):
        async with self._lock:
            self.counter += 1

            if self.counter < self.threshold:
                return

            self.counter = 0

            if self._training:
                return

        asyncio.create_task(self.retrain())