from typing import Any, Optional

from aiogram import types
from aiogram.exceptions import TelegramAPIError


class BaseBotException(Exception):
    def __init__(self, message: str, user_id: Optional[int] = None):
        self.message = message
        self.user_id = user_id
        super().__init__(message)


class DatabaseError(BaseBotException):
    pass


class APIError(BaseBotException):
    pass


class ValidationError(BaseBotException):
    pass


async def handle_error(
    error: Exception,
    message: Optional[types.Message] = None,
    logger: Optional[Any] = None
) -> None:
    error_message = 'Произошла ошибка. Пожалуйста, попробуйте позже.'
    
    if isinstance(error, BaseBotException):
        error_message = error.message
    elif isinstance(error, TelegramAPIError):
        error_message = 'Ошибка при отправке сообщения. Пожалуйста, попробуйте позже.'
    
    if logger:
        logger.error(f'Ошибка: {str(error)}', exc_info=True)
    
    if message:
        try:
            await message.answer(error_message)
        except Exception as e:
            if logger:
                logger.error(f'Не удалось отправить сообщение об ошибке: {str(e)}')
