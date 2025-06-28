import asyncio

import aiogram.exceptions

from bot import functions, keyboards
from config import settings
from utils.logger import setup_logger
from database.base import get_db
from database.repository.user import UserRepository
from database.repository.tracking import TrackingRepository

logger = setup_logger(__name__)


async def check_new_cars_task():
    logger.info('Запуск задачи проверки о появлений новых машин')

    async with get_db() as session:
        tracking_repo = TrackingRepository(session)
        tracking_list = await tracking_repo.tracking_list_all()
        user_repo = UserRepository(session)

        if tracking_list:
            for tracking in tracking_list:
                if tracking.is_active:
                    car_ids = await functions.parse_cars(session, tracking.id)
                    for car_id in car_ids:
                        if car_id not in tracking.car_ids:
                            try:
                                car_info = await functions.get_car_info_url(car_id)

                                car_age = functions.cal_car_age(
                                    int(str(car_info['cars']['base']['category']['yearMonth'])[:4]),
                                    str(car_info['cars']['base']['category']['yearMonth'])[4:]
                                )

                                msg = await functions.show_car_info(
                                    tracking.user_id,
                                    car_info,
                                    car_age,
                                    is_support=True
                                )

                                text = f'🔔 <b>Новый автомобиль по вашим параметрам!</b>'
                                kb = keyboards.new_car(car_id)

                                if isinstance(msg, list):
                                    await msg[0].reply(text, reply_markup=kb)
                                else:
                                    await msg.reply(text, reply_markup=kb)

                                user_info = await user_repo.get_user(tracking.user_id)

                                if user_info:
                                    username_text = f' @{user_info.username}' if user_info.username else ''
                                else:
                                    username_text = ''

                                while True:
                                    try:
                                        if user_info:
                                            text = f'<b>У пользователя {user_info.first_name}{username_text} (ID: {user_info.id})'
                                        else:
                                            text = f'<b>У пользователя (ID: {tracking.user_id})'

                                        text += f' появилось авто по его критериям</b>\n\n<a href="https://fem.encar.com/cars/detail/{car_id}">Ссылка на автомобиль</a>'

                                        await functions.show_track(
                                            settings.LOG_CHAT_ID,
                                            session,
                                            tracking.id,
                                            is_support=True,
                                            title=text
                                        )

                                        break
                                    except aiogram.exceptions.TelegramRetryAfter as time:
                                        await asyncio.sleep(time.retry_after + 1)

                                await asyncio.sleep(10)
                            except Exception as e:
                                logger.info(f'Ошибка отправки уведомления пользователю ({tracking.user_id}) о новом автомобиле ({car_id}) по его параметрам: {str(e)}')
                                await asyncio.sleep(1)

                    await tracking_repo.update_car_ids(tracking.id, list(set(tracking.car_ids + car_ids)))
                else:
                    await functions.activate_tracking(session, tracking.id)
        else:
            logger.info('Список отслеживаний на данный момент пуст')

    logger.info('Задача проверки о появлений новых машин выполнен')
