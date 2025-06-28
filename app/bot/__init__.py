import redis.asyncio as redis
from redis.backoff import ExponentialBackoff
from redis.asyncio.retry import Retry

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from config import settings

redis_client = redis.Redis(
    host='redis',
    port=6379,
    db=0,
    password=settings.REDIS_PASSWORD,
    decode_responses=True,
    retry=Retry(ExponentialBackoff(), retries=3),
    health_check_interval=30
)
storage = RedisStorage(redis_client)

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)
