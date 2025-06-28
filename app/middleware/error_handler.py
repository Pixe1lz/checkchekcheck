from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from aiogram.exceptions import TelegramAPIError

from utils.logger import setup_logger
from utils.exceptions import handle_error

logger = setup_logger(__name__)


class ErrorHandlerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Ошибка в обработчике: {str(e)}", exc_info=True)
            
            if isinstance(event, Message):
                await handle_error(e, event, logger)
            
            if isinstance(e, TelegramAPIError):
                logger.error(f"Ошибка Telegram API: {str(e)}")
            
            raise
