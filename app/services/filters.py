from aiogram.types import Message, CallbackQuery
from aiogram.filters import BaseFilter

from config import settings
from database.repository.user import UserRepository


class IsAdmin(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        if isinstance(event, Message):
            if event.chat.type != 'private':
                return False
        else:
            if event.message.chat.type != 'private':
                return False

        if event.from_user.id in settings.ADMIN_IDS:
            return True

        return False


class IsBlocked(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery, *args, **kwargs) -> bool:
        if isinstance(event, Message):
            if event.chat.type != 'private':
                return False
        else:
            if event.message.chat.type != 'private':
                return False

        user_repo = UserRepository(kwargs['session'])
        if await user_repo.is_blocked(event.from_user.id):
            text = '<b>Доступ к использованию бота был ограничен.</b>'

            if isinstance(event, Message):
                await event.answer(text)
            else:
                await event.message.delete()
                await event.message.answer(text)

            return False

        return True
