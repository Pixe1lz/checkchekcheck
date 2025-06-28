import asyncio
from urllib.parse import urlparse

import aiogram.exceptions
from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot import functions, keyboards
from bot.states import CarInfo
from services.filters import IsBlocked
from database.repository.car_viewing_history import CarViewingHistoryRepository

router = Router()


@router.callback_query(F.data.startswith('show_cars:'), IsBlocked())
async def show_cars(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    _, page, page_list = callback.data.split(':')
    page, page_list = int(page), int(page_list)

    data = await state.get_data()
    await callback.message.delete()
    if page_list in (0, 3):
        try:
            cars_info = await functions.get_cards(data, page, session)
        except KeyError:
            await callback.message.delete()
            return await callback.message.answer('<b>Бот был перезагружен. Повторите процесс повторно.</b>')

        await state.update_data(cars_info=cars_info)
        data = await state.get_data()

    await state.update_data(page=page, page_list=page_list)
    await functions.show_cars(callback, session, data['configuration_id'], data['cars_info'], page, page_list)


@router.callback_query(F.data.startswith('show_car:'), IsBlocked())
async def show_car(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    idx_car = int(callback.data.split(':')[-1])
    data = await state.get_data()

    car_info = data['cars_info']['cars'][data['page_list'] * 5:][idx_car]

    await callback.message.delete()

    car_age = functions.cal_car_age(
        int(str(int(car_info['Year']))[:4]),
        str(int(car_info['Year']))[4:]
    )

    await state.update_data(car_id=car_info['Id'], car_age=car_age)

    text, text_2 = await functions.get_car_info_text(car_info, car_age)

    if car_info['Photos']:
        media = []
        for i, photo in enumerate(car_info['Photos'][:10]):
            base_url = 'https://ci.encar.com/carpicture'
            if i == 0:
                media.append(
                    InputMediaPhoto(
                        media=base_url + photo['location'],
                        caption=text + text_2
                    )
                )
            else:
                media.append(InputMediaPhoto(media=base_url + photo['location']))

        try:
            await callback.message.answer_media_group(media=media)
        except aiogram.exceptions.TelegramBadRequest:
            media[0].caption = text
            await callback.message.answer_media_group(media=media)
            await callback.message.answer(text_2)
    else:
        await callback.message.answer(text)

    await asyncio.sleep(1)

    await callback.message.answer(
        text='Выберите дальнейшее действие',
        reply_markup=keyboards.create_statement(car_info['Id'], car_age, data['page'], data['page_list'])
    )

    car_view_repo = CarViewingHistoryRepository(session)
    await car_view_repo.save(callback.from_user.id, int(car_info['Id']))

    await functions.send_notification_to_admins(callback.from_user, 'рассчитал авто через каталог', car_info['Id'], car_age)


@router.callback_query(F.data == 'calc_link_encar', IsBlocked())
async def calc_link_encar(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        text='Пришлите ссылку на автомобиль на Encar.com. Например, https://fem.encar.com/cars/detail/39227500',
        reply_markup=keyboards.back('menu')
    )
    await state.set_state(CarInfo.url)


@router.message(F.text, CarInfo.url, IsBlocked())
async def url_validate(message: Message, state: FSMContext, session: AsyncSession):
    try:
        parsed_url = urlparse(message.text)

        if (
            parsed_url.hostname != 'fem.encar.com' or
            not parsed_url.path.startswith('/cars/detail/')
        ):
            return await message.answer('Неверная ссылка')

        path_parts = parsed_url.path.split('/')

        id_part = path_parts[-1] if path_parts[-1] else path_parts[-2]

        try:
            car_id = int(id_part)
        except ValueError:
            return await message.answer('Неверная ссылка')

    except Exception:
        return await message.answer('Неверная ссылка')

    car_info = await functions.get_car_info_url(car_id)
    if car_info:
        await state.clear()

        car_age = functions.cal_car_age(
            int(str(car_info['cars']['base']['category']['yearMonth'])[:4]),
            str(car_info['cars']['base']['category']['yearMonth'])[4:]
        )

        await functions.show_car_info(message.from_user.id, car_info, car_age)
        await state.update_data(car_id=car_id, car_age=car_age)

        car_view_repo = CarViewingHistoryRepository(session)
        await car_view_repo.save(message.from_user.id, car_id)

        await functions.send_notification_to_admins(message.from_user, 'рассчитал авто по ссылке', car_id, car_age)

    else:
        await message.answer('Ошибка получения информации по данной ссылке')


@router.callback_query(F.data == 'calc_link_encar_like_old', IsBlocked())
async def calc_link_encar_like_old(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    car_id = data['car_id']

    car_info = await functions.get_car_info_url(car_id)
    if car_info:
        await callback.message.delete()
        await functions.show_car_info(callback.from_user.id, car_info, {'year': 4, 'month': 0})
        await state.update_data(car_age=4)

        await functions.send_notification_to_admins(
            callback.from_user,
            'рассчитал авто по ссылке и нажал на кнопку (3-5 лет)',
            car_id,
            {'year': 4, 'month': 0}
        )
    else:
        await callback.message.answer('Ошибка получения информации по данному автомобилю')


@router.callback_query(F.data == 'calc_encar_like_old', IsBlocked())
async def calc_encar_like_old(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    try:
        car_id = data['car_id']
    except KeyError:
        await callback.message.answer('<b>Бот был перезагружен. Повторите процесс повторно.</b>')
        return

    car_info = await functions.get_car_info_url(car_id)
    if car_info:
        await callback.message.delete()
        await functions.show_car_info(callback.from_user.id, car_info, {'year': 4, 'month': 0}, is_url=False, state_data=data)
        await state.update_data(car_age=4)

        await functions.send_notification_to_admins(
            callback.from_user,
            'рассчитал авто через каталог и нажал на кнопку (3-5 лет)',
            car_id,
            {'year': 4, 'month': 0}
        )
    else:
        await callback.message.answer('Ошибка получения информации по данному автомобилю')
