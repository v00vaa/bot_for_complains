"""
Хранилище ролей пользователей.

Модуль отвечает за хранение и управление списком администраторов.

Все данные сохраняются в JSON-файл, благодаря чему изменения
сохраняются между перезапусками бота.

Особенности:
    • суперадминистратор задаётся в конфигурации (.env);
    • суперадминистратор никогда не записывается в JSON;
    • при запуске список администраторов загружается из файла,
      после чего автоматически добавляется суперадминистратор.
"""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_DIR = Path("config/data")

ADMINS_FILE = BASE_DIR / "admins.json"


class RolesStorage:
    """
    Хранилище ролей пользователей.

    Предоставляет методы для:
        • загрузки списка администраторов;
        • сохранения изменений;
        • добавления и удаления администраторов;
        • проверки прав пользователя.

    Данные кэшируются в памяти, поэтому проверки ролей
    выполняются без обращения к файловой системе.
    """
    def __init__(self, super_admin: int):
        """
        Создаёт объект хранилища.

        Args:
            super_admin:
                Telegram ID главного администратора,
                который задаётся в конфигурации приложения.
        """
        self.super_admin = super_admin

        self.admins: set[int] = set()

    def load(self) -> None:
        """
        Загружает список администраторов из файла.

        После загрузки автоматически добавляет
        суперадминистратора, чтобы он всегда имел
        полный доступ независимо от содержимого JSON.
        """
        self.admins = self._load_ids(ADMINS_FILE)

        self.admins.add(self.super_admin)

        logger.info(
            "Загружено %s администраторов",
            len(self.admins),
        )

    @staticmethod
    def _load_ids(path: Path) -> set[int]:
        """
        Загружает множество ID пользователей из JSON.

        Если файл отсутствует, он создаётся автоматически.

        Returns:
            Множество идентификаторов пользователей.
        """
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as file:
                json.dump([], file)

            return set()

        try:
            with open(path, encoding="utf-8") as file:
                return {int(user_id) for user_id in json.load(file)}

        except Exception as error:
            logger.error(
                "Ошибка чтения %s: %s",
                path,
                error,
            )
            return set()

    @staticmethod
    def _save_ids(path: Path, ids: set[int]) -> None:
        """
        Сохраняет множество ID пользователей в JSON.

        Перед сохранением список сортируется,
        чтобы файл было удобнее читать вручную.
        """
        with open(path, "w", encoding="utf-8") as file:
            json.dump(
                sorted(ids),
                file,
                ensure_ascii=False,
                indent=4,
            )

    def save(self) -> None:
        """
        Сохраняет текущий список администраторов.

        Суперадминистратор намеренно исключается
        из файла, поскольку хранится в конфигурации.
        """
        self._save_ids(
            ADMINS_FILE,
            self.admins - {self.super_admin},
        )

    # ---------- Admins ----------

    def add_admin(self, user_id: int) -> bool:
        """
        Добавляет нового администратора.

        Returns:
            True — пользователь успешно добавлен.
            False — пользователь уже является администратором.
        """
        if user_id in self.admins:
            return False

        self.admins.add(user_id)
        self.save()
        return True

    def remove_admin(self, user_id: int) -> bool:
        """
        Удаляет администратора.

        Суперадминистратор не может быть удалён.

        Returns:
            True — администратор удалён.
            False — операция невозможна.
        """
        if user_id == self.super_admin:
            return False

        if user_id not in self.admins:
            return False

        self.admins.remove(user_id)
        self.save()
        return True

    # ==========================================================
    # Проверка ролей
    # ==========================================================

    def is_admin(self, user_id: int) -> bool:
        """
        Проверяет, является ли пользователь администратором.
        """
        return user_id in self.admins

    def is_super_admin(self, user_id: int) -> bool:
        """
        Проверяет, является ли пользователь суперадминистратором.
        """
        return user_id == self.super_admin

    def get_admins(self) -> set[int]:
        """
        Возвращает копию списка администраторов.

        Используется копия множества, чтобы внешний код
        не мог случайно изменить внутреннее состояние
        хранилища.
        """
        return self.admins.copy()