from aiogram.filters import BaseFilter
from aiogram.types import Message


class TextKeyFilter(BaseFilter):
    def __init__(self, key: str):
        self.key = key

    async def __call__(
        self,
        message: Message,
        i18n: dict[str, str]
    ) -> bool:
        return message.text == i18n.get(self.key)
