from bot import bot
from config import settings
from utils.logger import setup_logger
from database.base import get_db
from database.repository.user import UserRepository

logger = setup_logger(__name__)


async def daily_statistics_task():
    logger.info('Запуск задачи отправка статистики по запускам бота')

    try:
        async with get_db() as session:
            user_repo = UserRepository(session)

            stats = await user_repo.get_statistics()

            await bot.send_message(
                chat_id=settings.STATISTICS_CHAT_ID,
                text=(
                    f'📊 <b>Статистика запусков бота</b>\n'
                    f'\n'
                    f'🔹 <i>За сегодня</i>: <b>{stats['today']}</b>\n'
                    f'🔹 <i>За вчера</i>: <b>{stats['yesterday']}</b>\n'
                    f'🔹 <i>За 3 дня</i>: <b>{stats['last_3_days']}</b>\n'
                    f'🔹 <i>За 7 дней</i>: <b>{stats['last_7_days']}</b>'
                )
            )

            logger.info('Задача по отправке сообщении статистики по запускам бота выполнена успешно')
    except Exception as e:
        logger.error(f'Ошибка отправки сообщения статистики по запускам бота: {str(e)}')
