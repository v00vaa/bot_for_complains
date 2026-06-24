from aiogram.filters import BaseFilter
from aiogram.types import Message


class IsSuperAdmin(BaseFilter):
    async def __call__(
        self,
        message: Message,
        roles,
    ) -> bool:
        return roles.is_super_admin(
            message.from_user.id
        )
