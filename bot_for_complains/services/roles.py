import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_DIR = Path("config/data")

ADMINS_FILE = BASE_DIR / "admins.json"


class RolesStorage:
    def __init__(self, super_admin: int):
        self.super_admin = super_admin

        self.admins: set[int] = set()

    def load(self) -> None:
        self.admins = self._load_ids(ADMINS_FILE)

        self.admins.add(self.super_admin)

        logger.info(
            "Загружено %s администраторов",
            len(self.admins),
        )

    @staticmethod
    def _load_ids(path: Path) -> set[int]:
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
        with open(path, "w", encoding="utf-8") as file:
            json.dump(
                sorted(ids),
                file,
                ensure_ascii=False,
                indent=4,
            )

    def save(self) -> None:
        self._save_ids(
            ADMINS_FILE,
            self.admins - {self.super_admin},
        )

    # ---------- Admins ----------

    def add_admin(self, user_id: int) -> bool:
        if user_id in self.admins:
            return False

        self.admins.add(user_id)
        self.save()
        return True

    def remove_admin(self, user_id: int) -> bool:
        if user_id == self.super_admin:
            return False

        if user_id not in self.admins:
            return False

        self.admins.remove(user_id)
        self.save()
        return True

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admins

    def is_super_admin(self, user_id: int) -> bool:
        return user_id == self.super_admin

    def get_admins(self) -> set[int]:
        return self.admins.copy()