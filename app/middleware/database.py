from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from database.base import get_db


class DatabaseMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[None]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        async with get_db() as session:
            data['session'] = session
            return await handler(event, data)
