from aiogram import BaseMiddleware

from bot import redis_client


class RedisCheckMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if not await redis_client.ping():
            raise ConnectionError('Redis недоступен')
        return await handler(event, data)
