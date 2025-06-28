import json
import asyncio
from datetime import datetime, UTC

import aiogram.exceptions
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, User
from aiogram.fsm.context import FSMContext
from aiogram.utils.deep_linking import create_start_link

import pytz
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession

from bot import bot, keyboards
from bot.states import CreateStatement
from config import settings
from services.utils import translator, AsyncHTTPClient
from database.repository.user import UserRepository
from database.repository.brand import BrandRepository
from database.repository.model import ModelRepository
from database.repository.generation import GenerationRepository
from database.repository.modification import ModificationRepository
from database.repository.configuration import ConfigurationRepository
from database.repository.tracking import TrackingRepository


async def menu(message_callback: Message | CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.clear()

    first_text = (
        f'<b>Привет, {message_callback.from_user.first_name}!</b>\n'
        f'Добро пожаловать в бот компании <a href="t.me/+UTL1yOM5WNY5YmFi">Alex Avto</a>\n'

    )
    second_text = (
        f'Данный бот синхронизирован с Encar, благодаря чему вы сможете быстро получить примерный расчет по интересующему вас автомобилю.\n'
        f'Для более точного просчета оставляйте заявку.\n'
        f'Давайте начнем - выбери необходимый раздел ниже.'
    )

    first_reply_markup = keyboards.menu()
    second_reply_markup = keyboards.inline_menu()

    if isinstance(message_callback, Message):
        await message_callback.answer(first_text, reply_markup=first_reply_markup)
        await message_callback.answer(second_text, reply_markup=second_reply_markup)
    else:
        await message_callback.message.delete()
        await message_callback.message.answer(first_text, reply_markup=first_reply_markup)
        await message_callback.message.answer(second_text, reply_markup=second_reply_markup)

    user_repo = UserRepository(session)
    if await user_repo.is_exist(message_callback.from_user.id):
        await user_repo.update_user(message_callback.from_user)
    else:
        await user_repo.create_user(message_callback.from_user)
        await send_notification_first_start_to_admins(message_callback.from_user)


async def show_brands(callback: CallbackQuery, state: FSMContext, page: int, session: AsyncSession):
    data = await state.get_data()
    brand_repo = BrandRepository(session)
    brands = await brand_repo.get_brands(page)

    await callback.message.delete()
    await callback.message.answer(
        text='Выберите марку автомобиля',
        reply_markup=keyboards.show_brands(brands, data.get('is_tracking', False), page)
    )


async def show_models(callback: CallbackQuery, brand_id: int, page: int, session: AsyncSession):
    model_repo = ModelRepository(session)
    models = await model_repo.get_models(brand_id, page)

    await callback.message.delete()
    await callback.message.answer(
        text='Выберите модель автомобиля',
        reply_markup=keyboards.show_models(models, brand_id, page)
    )


async def show_pre_check_auto(callback_message: CallbackQuery | Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    await state.clear()
    await state.update_data(data)

    brand_id = data['brand_id']
    model_id = data['model_id']
    generation_id = data['generation_id']
    modification_id = data['modification_id']
    configuration_id = data['configuration_id']
    release_year = data.get('release_year')
    mileage = data.get('mileage')
    price = data.get('price')
    is_tracking = data.get('is_tracking', False)

    if release_year:
        release_year_text = f'\nГод: {release_year}'
    else:
        release_year_text = ''

    if mileage:
        if '-' in mileage:
            mileage_start, mileage_end = mileage.split('-')
            mileage_start, mileage_end = int(mileage_start), int(mileage_end)
            mileage_text = f'\nПробег: {add_spaces_for_number(mileage_start)} - {add_spaces_for_number(mileage_end)} км.'
        else:
            mileage_text = f'\nПробег: от 0 до {add_spaces_for_number(mileage)} км.'
    else:
        mileage_text = ''

    if price:
        if '-' in price:
            price_start, price_end = price.split('-')
            price_start, price_end = int(price_start), int(price_end)

            price_text = f'\nЦена: {add_spaces_for_number(price_start)} - {add_spaces_for_number(price_end)} руб.'
        else:
            price_text = f'\nЦена: от 0 до {add_spaces_for_number(price)} руб.'
    else:
        price_text = ''

    brand_repo = BrandRepository(session)
    model_repo = ModelRepository(session)
    generation_repo = GenerationRepository(session)
    modification_repo = ModificationRepository(session)
    configuration_repo = ConfigurationRepository(session)

    text = (
        f'Проверьте выбранные параметры:\n'
        f'\n'
        f'Марка: {await brand_repo.get_brand_name(brand_id)}\n'
        f'Модель: {await model_repo.get_model_name(model_id)}\n'
        f'Поколение: {translator(await generation_repo.get_generation_name(generation_id))}\n'
        f'Модификация: {translator(await modification_repo.get_modification_name(modification_id))}\n'
        f'Комплектация: {translator(await configuration_repo.get_configuration_name(configuration_id))}'
        f'{release_year_text}'
        f'{mileage_text}'
        f'{price_text}'
    )

    reply_markup = keyboards.pre_check_auto(modification_id, is_tracking)

    if isinstance(callback_message, CallbackQuery):
        await callback_message.message.answer(text, reply_markup=reply_markup)
    else:
        await callback_message.answer(text, reply_markup=reply_markup)


async def get_cards(state_data: dict, page: int, session: AsyncSession) -> dict | None:
    configuration_repo = ConfigurationRepository(session)
    action = await configuration_repo.get_all_configuration_action(state_data['configuration_id'])

    if state_data.get('release_year'):
        if '-' in state_data['release_year']:
            start_year, end_year = state_data['release_year'].split('-')
            action = action[:-1] + ''
        else:
            action = action[:-1] + ''

    if state_data.get('mileage'):
        if '-' in state_data['mileage']:
            start_mileage, end_mileage = state_data['mileage'].split('-')
            action = action[:-1] + ''
        else:
            action = action[:-1] + ''

    async with AsyncHTTPClient('https://example') as client:
        data = await client.get(
            endpoint='/endpoint',
            params={
                'param': 'example',
            }
        )

    if data:
        return {
            'count': data['Count'],
            'cars': data['SearchResults']
        }


async def show_cars(callback: CallbackQuery, session: AsyncSession, configuration_id: int, cars_info: dict, page: int = 0, page_list: int = 0):
    await callback.message.answer(
        f'По запросу найдено {cars_info['count']} авто:',
        reply_markup=await keyboards.show_cars(
            callback.from_user.id,
            session,
            configuration_id,
            cars_info['cars'],
            cars_info['count'],
            page,
            page_list
        )
    )


def reformat_mileage_text(mileage: float) -> str:
    mileage = int(mileage)

    if mileage > 1_000:
        return f'{mileage // 1_000} тыс.км.'
    else:
        return f'{mileage} км.'


def reformat_price_text(price: int) -> str:
    price = int(price * 10_000)

    if price > 1_000_000:
        return f'{price // 1_000_000} млн.вон'
    elif price > 1_000:
        return f'{price // 1_000} тыс.вон'
    else:
        return f'{price} вон'


def reformat_price_text_2(price: int) -> str:
    if price > 1_000_000:
        return f'{round(price / 1_000_000, 1)} млн.'
    elif price > 1_000:
        return f'{round(price / 1_000, 1)} тыс.'
    else:
        return f'{price}'


def add_spaces_for_number(number: int | str) -> str:
    if number == '-':
        return number
    return f'{int(number):,}'.replace(',', ' ')


async def get_car_info_url(car_id: int | str) -> dict | None:
    async with AsyncHTTPClient('https://example') as client:
        html = await client.get(endpoint=f'/endpoint')

    soup = BeautifulSoup(html, 'html.parser')
    script_tag = soup.find('script', string=lambda text: '' in str(text))

    if script_tag:
        script_content = script_tag.string.split('' = ')[1].strip()
        car_info = json.loads(script_content)
        return car_info


async def get_engine_volume(car_id: str) -> int | None:
    car_info = await get_car_info_url(car_id)
    if car_info:
        return car_info['cars']['base']['spec']['displacement']


def cal_car_age(car_year: int, car_month: str) -> dict:
    current_date_now_utc = datetime.now(UTC)
    current_date_now_msc = current_date_now_utc.astimezone(pytz.timezone('Europe/Moscow'))
    total_month = (current_date_now_msc.year - car_year) * 12 + (current_date_now_msc.month - int(car_month))

    year = total_month // 12
    month = total_month % 12

    return {
        'year': year,
        'month': month
    }


def calc_recycling_fee(car_age: int, engine_volume: int, is_electro: bool, is_almost_old: bool) -> int:
    """
    https://customs.gov.ru/fiz/uplata-tamozhennyx-platezhej/uplata-utilizaczionnogo-sbora/utilizaczionnyj-sbor-na-kolesnye-transportnye-sredstva/ischislenie-utilizaczionnogo-sbora

    Пункт: В отношении легковых автомобилей для личного пользования
    """

    if is_almost_old:
        car_age += 1

    if car_age < 3:
        if is_electro:
            base_coefficient = 0.17
        else:
            if engine_volume < 1_000:
                base_coefficient = 0.17
            elif 1_000 <= engine_volume < 2_000:
                base_coefficient = 0.17
            elif 2_000 <= engine_volume < 3_000:
                base_coefficient = 0.17
            elif 3_000 <= engine_volume < 3_500:
                base_coefficient = 107.67
            else:
                base_coefficient = 137.11

    else:
        if is_electro:
            base_coefficient = 0.26
        else:
            if engine_volume < 1_000:
                base_coefficient = 0.26
            elif 1_000 <= engine_volume < 2_000:
                base_coefficient = 0.26
            elif 2_000 <= engine_volume < 3_000:
                base_coefficient = 0.26
            elif 3_000 <= engine_volume < 3_500:
                base_coefficient = 164.84
            else:
                base_coefficient = 180.24

    recycling_fee = 20_000 * base_coefficient  # Утилизационный сбор

    return int(recycling_fee)


def calc_custom_duty(car_age: int, car_price: int, engine_volume: int, is_almost_old: bool) -> int:
    """https://customs.gov.ru/fiz/pravila-peremeshheniya-tovarov/transportnye-sredstva/vvoz-transportnyx-sredstv-dlya-lichnogo-pol-zovaniya/stavki-tamozhennyx-poshlin,-nalogov-v-otnoshenii-transportnyx-sredstv-dlya-lichnogo-pol-zovaniya"""
    if is_almost_old:
        car_age += 1

    if car_age < 3:
        euro_price = car_price / settings.EUR_RATE
        multiplier = 0.48

        if euro_price < 8_500:
            custom_duty = engine_volume * 2.5
            multiplier = 0.54
        elif 8_500 <= euro_price < 16_700:
            custom_duty = engine_volume * 3.5
        elif 16_700 <= euro_price < 42_300:
            custom_duty = engine_volume * 5.5
        elif 42_300 <= euro_price < 84_500:
            custom_duty = engine_volume * 7.5
        elif 84_500 <= euro_price < 169_000:
            custom_duty = engine_volume * 15
        else:
            custom_duty = engine_volume * 20

        if car_price * multiplier > custom_duty * settings.EUR_RATE:
            return int(car_price * multiplier)
        else:
            return int(custom_duty * settings.EUR_RATE)

    elif 3 <= car_age < 5:
        if engine_volume < 1_000:
            custom_duty = engine_volume * 1.5
        elif 1_000 <= engine_volume < 1_500:
            custom_duty = engine_volume * 1.7
        elif 1_500 <= engine_volume < 1_800:
            custom_duty = engine_volume * 2.5
        elif 1_800 <= engine_volume < 2_300:
            custom_duty = engine_volume * 2.7
        elif 2_300 <= engine_volume < 3_000:
            custom_duty = engine_volume * 3
        else:
            custom_duty = engine_volume * 3.6
    else:
        if engine_volume < 1_000:
            custom_duty = engine_volume * 3
        elif 1_000 <= engine_volume < 1_500:
            custom_duty = engine_volume * 3.2
        elif 1_500 <= engine_volume < 1_800:
            custom_duty = engine_volume * 3.5
        elif 1_800 <= engine_volume < 2_300:
            custom_duty = engine_volume * 4.8
        elif 2_300 <= engine_volume < 3_000:
            custom_duty = engine_volume * 5
        else:
            custom_duty = engine_volume * 5.7

    custom_duty = custom_duty * settings.EUR_RATE  # Таможенная пошлина
    return int(custom_duty)


def calc_custom_clearance(car_price: int) -> int:
    # Таможенное оформление

    if car_price <= 200_000:
        return 1_067
    elif 200_000.01 <= car_price <= 450_000:
        return 2_134
    elif 450_000.01 <= car_price <= 1_200_000:
        return 4_269
    elif 1_200_000.01 <= car_price <= 2_700_000:
        return 11_746
    elif 2_700_000.01 <= car_price <= 4_200_000:
        return 16_524
    elif 4_200_000.01 <= car_price <= 5_500_000:
        return 21_344
    elif 5_500_000.01 <= car_price <= 7_000_000:
        return 27_540
    else:
        return 30_000


async def get_car_info_text(car_info: dict, car_age: dict, is_url: bool = False):
    if is_url:
        brand_name = car_info['cars']['base']['category']['manufacturerEnglishName']
        model_name = car_info['cars']['base']['category']['modelName']
        grade_name = car_info['cars']['base']['category']['gradeEnglishName']

        form_year = int(str(car_info['cars']['base']['category']['yearMonth'])[:4])
        form_month = str(car_info['cars']['base']['category']['yearMonth'])[4:]

        mileage = car_info['cars']['base']['spec']['mileage']

        fuel_type = car_info['cars']['base']['spec']['fuelName']

        car_price = int(car_info['cars']['base']['advertisement']['price'] * 10_000)

        car_id = car_info['cars']['base']['queryCarId']

        engine_volume = car_info['cars']['base']['spec']['displacement']
    else:
        brand_name = car_info['Manufacturer']
        model_name = car_info['Model']
        grade_name = car_info['Badge']

        form_year = int(str(int(car_info['Year']))[:4])
        form_month = str(int(car_info['Year']))[4:]

        mileage = int(car_info['Mileage'])

        fuel_type = car_info['FuelType']

        car_price = int(car_info['Price'] * 10_000)

        car_id = car_info['Id']

        engine_volume = await get_engine_volume(car_id)

    is_new = False
    is_almost_old = False
    if car_age['year'] < 3:
        is_new = True

        if car_age['year'] == 2 and car_age['month'] + 8 >= 12:
            is_almost_old = True


    if is_new:
        if is_almost_old:
            faq_text = (
                f'<i>'
                f'🔴 Данное авто посчитано по проходной таможенной ставке 3-5 лет.\n'
                f'После покупки, авто ставится на нашу подземную стоянку и как наступает дата - отправляется в Россию.\n'
                f'Для вас это бесплатно.'
                f'</i>\n'
                f'\n'
            )
        else:
            faq_text = (
                f'<i>'
                f'🔴 В Ю.Корее указывается дата постановки на учет.\n'
                f'Дата производства может отличаться в среднем на 3-4 месяца.\n'
                f'Для расчета авто как проходной 3-5 лет, нажмите кнопку ниже.'
                f'</i>\n'
                f'\n'
            )
    else:
        faq_text = ''

    car_price_rub = int(car_price * settings.KRW_RATE)

    if engine_volume:
        engine_volume_text = f'<b>Объем двигателя (см3)</b>: {engine_volume}\n'

        recycling_fee = calc_recycling_fee(
            car_age['year'],
            engine_volume,
            fuel_type == '전기',
            is_almost_old
        )

        custom_duty = calc_custom_duty(
            car_age['year'],
            car_price_rub,
            engine_volume,
            is_almost_old
        )
    else:
        engine_volume_text = ''
        recycling_fee = '-'
        custom_duty = '-'

    custom_clearance = calc_custom_clearance(car_price_rub)

    delivery_to_Vladivostok = int((car_price + 2_400_000) * settings.KRW_RATE)

    final_price = delivery_to_Vladivostok + custom_clearance + 110_000 + 150_000
    if recycling_fee != '-':
        final_price += recycling_fee + custom_duty

    return (
        f'<b>{translator(brand_name)} {translator(model_name)} {translator(grade_name)}</b>\n'
        f'\n'
        f'<b>Дата выпуска (год/месяц)</b>: {form_year}/{form_month}\n'
        f'<b>Пробег</b>: {add_spaces_for_number(mileage)} км.\n'
        f'<b>Топливо</b>: {translator(fuel_type)}\n'
        f'{engine_volume_text}'
        f'\n'
        f'<b>Итого: {add_spaces_for_number(int(final_price))} руб.* - стоимость автомобиля во Владивостоке со всеми расходами (под ключ)</b>\n'
        f'<blockquote>'
        f'* не учтена комиссия на покупку валюту, для точного рассчета обратитесь к менеджеру'
        f'</blockquote>\n'
        f'\n'
        f'<a href="{await create_start_link(bot, str(car_id), encode=True)}">Сделать точный рассчет</a>\n'
        f'\n'
        f'{faq_text}'
        f'<blockquote><i>'
        f'Этапы оплаты/включено в стоимость:\n'
        f'1. Выкуп авто в Ю.Корее (KRW) {reformat_price_text_2(car_price)}\n'
        f'+ доставка во Владивосток (KRW) 2.4 млн.\n'
        f'= {add_spaces_for_number(delivery_to_Vladivostok)} (RUB)\n'
        f'Сроки доставки во Владивосток 8-14 дней\n'
        f'\n'
        f'2. Оплата Тамож. пошлина (RUB) {add_spaces_for_number(custom_duty)}\n'
        f'Утиль. сбор (RUB): {add_spaces_for_number(recycling_fee)}\n'
        f'Тамож. оформление (RUB): {add_spaces_for_number(custom_clearance)}\n'
        f'Услуги брокера (RUB): 110 000\n'
        f'Комиссия: Alex Avto (RUB): 150 000\n'
        f'\n'
        f'3. Автовоз: рассчитывается отдельно\n'
        f'Сроки доставки от границы в ваш город 7-14 дней'
        f'</i></blockquote>\n'
        f'\n'
        f'<a href="https://fem.encar.com/cars/detail/{car_id}">Ссылка на авто</a>\n'
        f'<a href="t.me/alex_gornostaev">Связаться с нами</a>\n'
        f'<a href="t.me/+UTL1yOM5WNY5YmFi">Канал Alex Avto</a>\n'
        f'\n'
    ), (
        f'<blockquote>'
        f'Расчет является предварительным.\n'
        f'Итоговая стоимость будет зависеть от курса валют на момент оплаты и может незначительно отличаться.\n'
        f'Так же возможны ошибки расчета, для более точной оценке оставьте заявку.'
        f'</blockquote>'
    )


async def show_car_info(chat_id: int, car_info: dict, car_age: dict, is_support: bool = False, is_url: bool = True, state_data: dict = None) -> Message | list[Message]:
    if state_data is None:
        state_data = {}

    text, text_2 = await get_car_info_text(car_info, car_age, is_url)

    if car_info['cars']['base']['photos']:
        media = []
        for photo in car_info['cars']['base']['photos']:
            if photo['type'] == 'OUTER':
                base_url = 'https://example'
                if media:
                    media.append(InputMediaPhoto(media=base_url + photo['path']))
                else:
                    media.append(
                        InputMediaPhoto(
                            media=base_url + photo['path'],
                            caption=text + text_2
                        )
                    )

        try:
            msg = await bot.send_media_group(
                chat_id=chat_id,
                media=media[:10]
            )
        except aiogram.exceptions.TelegramBadRequest:
            media[0].caption = text
            msg = await bot.send_media_group(
                chat_id=chat_id,
                media=media
            )
            await bot.send_message(
                chat_id=chat_id,
                text=text_2
            )
    else:
        msg = await bot.send_message(
            chat_id=chat_id,
            text=text
        )

    if not is_support:
        await asyncio.sleep(1)

        next_info_text = 'Выберите дальнейшее действие'

        if is_url:
            next_info_kb = keyboards.create_statement_2(car_info['Id'], car_age)
        else:
            next_info_kb = keyboards.create_statement(car_info['Id'], car_age, state_data('page', 0), state_data('page_list', 0))

        await bot.send_message(
            chat_id=chat_id,
            text=next_info_text,
            reply_markup=next_info_kb
        )

    return msg


async def show_my_tracking(callback: CallbackQuery, tracking_count: int, session: AsyncSession, page: int = 0):
    tracking_repo = TrackingRepository(session)
    tracking_list = await tracking_repo.tracking_list(callback.from_user.id, page)

    await callback.message.delete()
    await callback.message.answer(
        '<b>Ваши отслеживания</b>',
        reply_markup=await keyboards.show_my_tracking_list(tracking_list, tracking_count, page, session)
    )


async def show_track(chat_id: int, session: AsyncSession, track_id: int, is_support: bool = False, title: str = ''):
    brand_repo = BrandRepository(session)
    model_repo = ModelRepository(session)
    generation_repo = GenerationRepository(session)
    modification_repo = ModificationRepository(session)
    configuration_repo = ConfigurationRepository(session)
    tracking_repo = TrackingRepository(session)

    track_info = await tracking_repo.track_get(track_id)

    modification_id = await configuration_repo.get_modification_id(track_info.configuration_id)
    generation_id = await modification_repo.get_generation_id(modification_id)
    model_id = await generation_repo.get_model_id(generation_id)
    brand_id = await model_repo.get_brand_id(model_id)
    configuration_id = track_info.configuration_id

    release_year = track_info.release_year
    mileage = track_info.mileage
    price = track_info.price

    if release_year:
        release_year_text = f'\nГод: {release_year}'
    else:
        release_year_text = ''

    if mileage:
        if '-' in mileage:
            mileage_start, mileage_end = mileage.split('-')
            mileage_start, mileage_end = int(mileage_start), int(mileage_end)
            mileage_text = f'\nПробег: {add_spaces_for_number(mileage_start)} - {add_spaces_for_number(mileage_end)} км.'
        else:
            mileage_text = f'\nПробег: от 0 до {add_spaces_for_number(mileage)} км.'
    else:
        mileage_text = ''

    if price:
        if '-' in price:
            price_start, price_end = price.split('-')
            price_start, price_end = int(price_start), int(price_end)

            price_text = f'\nЦена: {add_spaces_for_number(price_start)} - {add_spaces_for_number(price_end)} руб.'
        else:
            price_text = f'\nЦена: от 0 до {add_spaces_for_number(price)} руб.'
    else:
        price_text = ''

    text = (
        f'{f'{title}\n\n' if title else ''}'
        f'Марка: {await brand_repo.get_brand_name(brand_id)}\n'
        f'Модель: {await model_repo.get_model_name(model_id)}\n'
        f'Поколение: {translator(await generation_repo.get_generation_name(generation_id))}\n'
        f'Модификация: {translator(await modification_repo.get_modification_name(modification_id))}\n'
        f'Комплектация: {translator(await configuration_repo.get_configuration_name(configuration_id))}'
        f'{release_year_text}'
        f'{mileage_text}'
        f'{price_text}'
    )

    reply_markup = keyboards.show_track(track_id)

    if is_support:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            disable_notification=True
        )
    else:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup
        )


async def parse_cars(session: AsyncSession, track_id: int) -> list[int]:
    track_repo = TrackingRepository(session)
    configuration_repo = ConfigurationRepository(session)

    track_info = await track_repo.track_get(track_id)
    configuration_action = await configuration_repo.get_action(track_info.configuration_id)

    if track_info.release_year:
        if '-' in track_info.release_year:
            start_year, end_year = track_info.release_year.split('-')
            configuration_action = configuration_action[:-1] + ''
        else:
            configuration_action = configuration_action[:-1] + ''

    if track_info.mileage:
        if '-' in track_info.mileage:
            start_mileage, end_mileage = track_info.mileage.split('-')
            configuration_action = configuration_action[:-1] + ''
        else:
            configuration_action = configuration_action[:-1] + ''

    def add_comma_for_number(number: int | float) -> str:
        if isinstance(number, int):
            integer_part = number
            fractional_part = 0
        else:
            str_num = str(number)
            if '.' in str_num:
                integer_part_str, fractional_part_str = str_num.split('.', 1)
                integer_part = int(integer_part_str)
                fractional_part = int(fractional_part_str.ljust(3, '0')[:3])
            else:
                integer_part = number
                fractional_part = 0

        formatted_number = f'{integer_part},{fractional_part:03d}'
        return formatted_number

    if track_info.price:
        if '-' in track_info.price:
            start_price, end_price = track_info.price.split('-')
            start_price, end_price = int(start_price), int(end_price)

            start_price = start_price * settings.KRW_RATE / 10_000
            end_price = end_price * settings.KRW_RATE / 10_000
            configuration_action = configuration_action[:-1] + ''
        else:
            KRW_price = int(track_info.price) * settings.KRW_RATE / 10_000
            configuration_action = configuration_action[:-1] + ''

    car_ids = []
    offset = 0

    async with AsyncHTTPClient('https://example') as client:
        while True:
            await asyncio.sleep(1)

            cars = await client.get(
                endpoint='/endpoint',
                params={
                    'param': 'example',
                }
            )

            offset += 20

            if cars:
                if cars.get('SearchResults'):
                    for car in cars['SearchResults']:
                        car_ids.append(int(car['Id']))

                    if cars['Count'] < offset:
                        break
                else:
                    break
            else:
                break

    return car_ids


async def activate_tracking(session: AsyncSession, track_id: int):
    car_ids = await parse_cars(session, track_id)
    tracking_repo = TrackingRepository(session)
    await tracking_repo.update_car_ids(track_id, car_ids)
    await tracking_repo.activate_track(track_id)


async def send_notification_to_admins(user_info: User, additional_text: str, car_id: int | str, car_age: dict) -> None:
    username_text = f' @{user_info.username}' if user_info.username else ''

    text = (
        f'Пользователь <a href="tg://user?id={user_info.id}">{user_info.first_name}</a>{username_text} (ID: {user_info.id}) {additional_text}'
    )

    car_info = await get_car_info_url(car_id)

    while True:
        try:
            msg = await show_car_info(settings.LOG_CHAT_ID, car_info, car_age, is_support=True)
            break
        except aiogram.exceptions.TelegramRetryAfter as time:
            await asyncio.sleep(time.retry_after + 1)

    while True:
        try:
            if isinstance(msg, list):
                await msg[0].reply(text)
            else:
                await msg.reply(text)

            break
        except aiogram.exceptions.TelegramRetryAfter as time:
            await asyncio.sleep(time.retry_after + 1)


async def send_notification_statement_to_admins(user_info: User, car_id: int, car_age: dict, statement_name: str, statement_contact: str):
    car_info = await get_car_info_url(car_id)

    username_text = f' @{user_info.username}' if user_info.username else ''

    text = (
        f'🟢🟢🟢\n'
        f'Пользователь <a href="tg://user?id={user_info.id}">{user_info.first_name}</a>{username_text} (ID: {user_info.id}) оставил заявку точного рассчета на автомобиль\n'
        f'Имя: {statement_name}\n'
        f'Контакт: {statement_contact}\n'
        f'{f'Тег TG:{username_text}' if username_text else ''}\n'
        f'\n'
        f'@team_alexavto'
    )

    while True:
        try:
            msg = await show_car_info(settings.LOG_CHAT_ID, car_info, car_age, is_support=True)
            break
        except aiogram.exceptions.TelegramRetryAfter as time:
            await asyncio.sleep(time.retry_after + 1)

    while True:
        try:
            if isinstance(msg, list):
                await msg[0].reply(text)
            else:
                await msg.reply(text)

            break
        except aiogram.exceptions.TelegramRetryAfter as time:
            await asyncio.sleep(time.retry_after + 1)

    while True:
        try:
            msg_2 = await show_car_info(settings.STATEMENT_CHAT_ID, car_info, car_age, is_support=True)
            break
        except aiogram.exceptions.TelegramRetryAfter as time:
            await asyncio.sleep(time.retry_after + 1)

    while True:
        try:
            if isinstance(msg_2, list):
                await msg_2[0].reply(text)
            else:
                await msg_2.reply(text)

            break
        except aiogram.exceptions.TelegramRetryAfter as time:
            await asyncio.sleep(time.retry_after + 1)


async def send_notification_first_start_to_admins(user_info: User):

    username_text = f' @{user_info.username}' if user_info.username else ''
    text = f'<b>Пользователь <a href="tg://user?id={user_info.id}">{user_info.first_name}</a>{username_text} (ID: {user_info.id}) запустил бота</b>'

    while True:
        try:
            await bot.send_message(settings.LOG_CHAT_ID, text)
            break
        except aiogram.exceptions.TelegramRetryAfter as time:
            await asyncio.sleep(time.retry_after + 1)


async def create_statement(callback_message: CallbackQuery | Message, state: FSMContext):
    text = 'Напишите, как Вас зовут?'

    if isinstance(callback_message, CallbackQuery):
        await callback_message.message.delete()
        await callback_message.message.answer(text)
    else:
        await callback_message.delete()
        await callback_message.answer(text)

    await state.set_state(CreateStatement.name)