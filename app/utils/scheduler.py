import asyncio

import pytz
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from utils.logger import setup_logger

logger = setup_logger(__name__)


class Scheduler:
    def __init__(self, timezone: str = 'Europe/Moscow'):
        logger.info(f'Инициализация планировщика с часовым поясом: {timezone}')
        self.timezone = pytz.timezone(timezone)
        self.scheduler = AsyncIOScheduler(
            jobstores={
                'default': MemoryJobStore()
            },
            executors={
                'default': ThreadPoolExecutor(20),
                'async': AsyncIOExecutor()
            },
            job_defaults={
                'coalesce': False,
                'max_instances': 3,
                'misfire_grace_time': 60
            },
            timezone=self.timezone
        )
        logger.info('Планировщик инициализирован')
    
    def start(self):
        try:
            self.scheduler.start()
            logger.info(f'Планировщик задач запущен (временная зона: {self.timezone})')
            logger.info(f'Активные задачи: {self.scheduler.get_jobs()}')
        except Exception as e:
            logger.error(f'Ошибка при запуске планировщика: {str(e)}')
            raise
    
    def shutdown(self):
        try:
            self.scheduler.shutdown()
            logger.info('Планировщик задач остановлен')
        except Exception as e:
            logger.error(f'Ошибка при остановке планировщика: {str(e)}')
            raise
    
    def add_job(self, func, trigger, **kwargs):
        try:
            if isinstance(trigger, str):
                if trigger == 'cron':
                    trigger = CronTrigger(
                        timezone=self.timezone,
                        **{k: v for k, v in kwargs.items() if k in CronTrigger.__init__.__code__.co_varnames}
                    )
                elif trigger == 'interval':
                    trigger = IntervalTrigger(
                        **{k: v for k, v in kwargs.items() if k in IntervalTrigger.__init__.__code__.co_varnames}
                    )
            
            if asyncio.iscoroutinefunction(func):
                kwargs['executor'] = 'async'
            
            next_run_time = kwargs.pop('next_run_time', None)
            
            job = self.scheduler.add_job(
                func,
                trigger=trigger,
                next_run_time=next_run_time,
                **kwargs
            )
            logger.info(f'Задача {func.__name__} добавлена с триггером {trigger}')
            if job.next_run_time:
                logger.info(f'Следующий запуск задачи: {job.next_run_time}')
            return job
        except Exception as e:
            logger.error(f'Ошибка при добавлении задачи {func.__name__}: {str(e)}')
            raise


scheduler = Scheduler(timezone='Europe/Moscow')
