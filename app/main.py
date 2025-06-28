import asyncio
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

import pytz

from bot import bot, dp
from bot.handlers import router

from database.base import engine
from database.models import *

from utils.logger import setup_logger
from utils.scheduler import scheduler

from tasks.auth_encar import auth_encar_task
from tasks.check_new_cars import check_new_cars_task
from tasks.currency_update import KRW_updates_task
from tasks.daily_parsing import daily_parsing_task
from tasks.daily_statistics import daily_statistics_task

from middleware.database import DatabaseMiddleware
from middleware.error_handler import ErrorHandlerMiddleware
from middleware.redis import RedisCheckMiddleware

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan():
    try:
        scheduler.start()

        current_time = datetime.now(pytz.timezone('Europe/Moscow'))

        next_run_time_for_daily_tasks = current_time.replace(hour=0, minute=0, second=0)
        if next_run_time_for_daily_tasks < current_time:
            next_run_time_for_daily_tasks += timedelta(days=1)

        scheduler.add_job(
            daily_statistics_task,
            trigger='cron',
            hour=0,
            minute=0,
            second=0,
            next_run_time=next_run_time_for_daily_tasks,
            id='daily_statistics',
        )

        scheduler.add_job(
            daily_parsing_task,
            trigger='cron',
            hour=0,
            minute=0,
            second=0,
            next_run_time=next_run_time_for_daily_tasks,
            id='daily_parsing'
        )

        scheduler.add_job(
            auth_encar_task,
            trigger='interval',
            hours=8,
            next_run_time=current_time,
            id='auth_encar'
        )

        scheduler.add_job(
            KRW_updates_task,
            trigger='interval',
            hours=1,
            next_run_time=current_time,
            id='KRW_updates'
        )

        scheduler.add_job(
            check_new_cars_task,
            trigger='interval',
            minutes=30,
            next_run_time=datetime.now(pytz.timezone('Europe/Moscow')),
            id='check_new_cars'
        )

        logger.info('Запуск бота')
        yield
    except Exception as e:
        logger.error(f'Ошибка при запуске бота: {str(e)}')
        raise
    finally:
        scheduler.shutdown()
        logger.info('Отключение бота')


async def main():
    dp.update.middleware(DatabaseMiddleware())
    dp.update.middleware(ErrorHandlerMiddleware())
    dp.update.middleware(RedisCheckMiddleware())
    dp.include_routers(router)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with lifespan():
        await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Бот остановлен пользователем')
    except Exception as e:
        logger.error(f'Не предвиденная ошибка {str(e)}')
