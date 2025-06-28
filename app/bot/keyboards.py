from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from bot.functions import reformat_mileage_text, reformat_price_text
from services.utils import translator
from database.models import Tracking
from database.repository.brand import BrandRepository
from database.repository.model import ModelRepository
from database.repository.generation import GenerationRepository
from database.repository.modification import ModificationRepository
from database.repository.configuration import ConfigurationRepository
from database.repository.car_viewing_history import CarViewingHistoryRepository


def menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Главное меню')]
        ],
        resize_keyboard=True
    )


def inline_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='🚗 Подобрать авто из Кореи', callback_data='choice_car')],
            [InlineKeyboardButton(text='🔔 Отслеживание новых предложений', callback_data='tracking_menu')],
            [InlineKeyboardButton(text='Какие авто выгодны?', callback_data='faq')],
            [InlineKeyboardButton(text='👥 О команде Alex Avto', url='t.me/+UTL1yOM5WNY5YmFi')]
        ]
    )


def choice_format():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='🔎 Поиск в каталоге', callback_data='choice_brand:0')],
            [InlineKeyboardButton(text='🔗 Расчет по ссылке Encar', callback_data='calc_link_encar')],
            [InlineKeyboardButton(text='🔙 Назад', callback_data='menu')]
        ]
    )


#  FIXME Сделать нормальную пагинацию
def show_brands(brands: list[tuple], is_tracking: bool, page: int):
    kb = InlineKeyboardMarkup(inline_keyboard=[])

    for brand_id, brand_eng_name in brands:
        kb.inline_keyboard.append(
            [InlineKeyboardButton(text=brand_eng_name, callback_data=f'choice_model:{brand_id}:0')]
        )

    if page == 0:
        kb.inline_keyboard.append(
            [InlineKeyboardButton(text='Вперед ➡️', callback_data=f'choice_brand:{page + 1}')]
        )
    elif len(brands) < 5:
        kb.inline_keyboard.append(
            [InlineKeyboardButton(text='⬅️ Назад', callback_data=f'choice_brand:{page - 1}')]
        )
    else:
        kb.inline_keyboard.append(
            [
                InlineKeyboardButton(text='⬅️ Назад', callback_data=f'choice_brand:{page - 1}'),
                InlineKeyboardButton(text='Вперед ➡️', callback_data=f'choice_brand:{page + 1}'),
            ]
        )

    kb.inline_keyboard.append(
        [InlineKeyboardButton(text='К предыдущему пункту ◀️', callback_data='tracking_menu' if is_tracking else 'choice_car')]
    )

    return kb


#  FIXME Сделать нормальную пагинацию
def show_models(models: list[tuple], brand_id: int, page: int):
    kb = InlineKeyboardMarkup(inline_keyboard=[])

    for model_id, model_eng_name in models:
        kb.inline_keyboard.append(
            [InlineKeyboardButton(text=model_eng_name, callback_data=f'choice_generation:{model_id}')]
        )

    if page == 0:
        kb.inline_keyboard.append(
            [InlineKeyboardButton(text='Вперед ➡️', callback_data=f'choice_model:{brand_id}:{page + 1}')]
        )
    elif len(models) < 5:
        kb.inline_keyboard.append(
            [InlineKeyboardButton(text='⬅️ Назад', callback_data=f'choice_model:{brand_id}:{page - 1}')]
        )
    else:
        kb.inline_keyboard.append(
            [
                InlineKeyboardButton(text='⬅️ Назад', callback_data=f'choice_model:{brand_id}:{page - 1}'),
                InlineKeyboardButton(text='Вперед ➡️', callback_data=f'choice_model:{brand_id}:{page + 1}'),
            ]
        )

    kb.inline_keyboard.append(
        [InlineKeyboardButton(text='К предыдущему пункту ◀️', callback_data='choice_brand:0')]
    )

    return kb


def show_generation(brand_id: int, generations: list[tuple]):
    kb = InlineKeyboardMarkup(inline_keyboard=[])

    for generation_id, display_value, start_year, end_year in generations:
        if start_year:
            if end_year:
                years = f' ({start_year} - {end_year})'
            else:
                years = f' ({start_year} - наст.вр.)'
        else:
            years = ''

        kb.inline_keyboard.append(
            [InlineKeyboardButton(text=f'{translator(display_value)}{years}', callback_data=f'choice_modification:{generation_id}')]
        )

    kb.inline_keyboard.append(
        [InlineKeyboardButton(text='К предыдущему пункту ◀️', callback_data=f'choice_model:{brand_id}:0')]
    )

    return kb


def show_modification(model_id: int, modifications: list[tuple]):
    kb = InlineKeyboardMarkup(inline_keyboard=[])

    for modification_id, display_value in modifications:
        kb.inline_keyboard.append(
            [InlineKeyboardButton(text=translator(display_value), callback_data=f'choice_configuration:{modification_id}')]
        )

    kb.inline_keyboard.append(
        [InlineKeyboardButton(text='К предыдущему пункту ◀️', callback_data=f'choice_generation:{model_id}')]
    )

    return kb


def show_configuration(generation_id: int, configuration_info: list[tuple]):
    kb = InlineKeyboardMarkup(inline_keyboard=[])

    for configuration_id, display_value, model_count in configuration_info:
        kb.inline_keyboard.append(
            [InlineKeyboardButton(text=f'{translator(display_value)} - {model_count} шт.', callback_data=f'pre_check_auto:{configuration_id}')]
        )

    kb.inline_keyboard.append(
        [InlineKeyboardButton(text='К предыдущему пункту ◀️', callback_data=f'choice_modification:{generation_id}')]
    )

    return kb


def pre_check_auto(modification_id: int, is_tracking: bool):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✅ Всё верно', callback_data='save_tracking' if is_tracking else 'confirm')],
            [InlineKeyboardButton(text='➕ Добавить фильтр - год выпуска', callback_data='add_release_year')],
            [InlineKeyboardButton(text='➕ Добавить фильтр - пробег', callback_data='add_mileage')],
            [InlineKeyboardButton(text='◀️ К предыдущему пункту', callback_data=f'choice_configuration:{modification_id}')],
            [InlineKeyboardButton(text='🔙 Начать заново', callback_data='choice_brand:0')]
        ]
    )

    if is_tracking:
        kb.inline_keyboard.insert(
            3,
            [InlineKeyboardButton(text='➕ Добавить фильтр - цена', callback_data='add_price')]
        )

    return kb


async def show_cars(user_id: int, session: AsyncSession, configuration_id: int, cars: list[dict], cars_count: int, page: int, page_list: int):
    car_view_repo = CarViewingHistoryRepository(session)
    kb = InlineKeyboardMarkup(inline_keyboard=[])

    car_idx = 0
    for idx, car in enumerate(cars[page_list * 5:page_list * 5 + 5], start=page_list * 5):
        is_viewed = False

        if await car_view_repo.is_viewed(user_id, int(car['Id'])):
            is_viewed = True

        kb.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=f'{idx + 1}. {reformat_mileage_text(car['Mileage'])} {reformat_price_text(car['Price'])} ({car['FormYear']} г.в.) {'✅' if is_viewed else ''}',
                    callback_data=f'show_car:{car_idx}'
                )
            ]
        )
        car_idx += 1

    pgn_btn = []

    if page != 0 or page_list != 0:
        pgn_btn.append(InlineKeyboardButton(
            text='⬅️ Назад',
            callback_data=f'show_cars:{page - 1 if page_list == 0 else page}:{3 if page_list == 0 else page_list - 1}')
        )

    if cars_count > (page * 20) + (page_list * 5 + 5):
        pgn_btn.append(InlineKeyboardButton(
            text='Далее ➡️',
            callback_data=f'show_cars:{page + 1 if page_list == 3 else page}:{0 if page_list == 3 else page_list + 1}')
        )

    if pgn_btn:
        kb.inline_keyboard.append(pgn_btn)

    kb.inline_keyboard.append(
        [InlineKeyboardButton(text='К предыдущему пункту ◀️', callback_data=f'pre_check_auto:{configuration_id}')]
    )

    return kb


def create_statement(car_id: int, car_age: dict, page: int, page_list: int):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Создать заявку 🔥', callback_data=f'create_statement:{car_id}')],
            [InlineKeyboardButton(text='Вернуться к списку 🔙', callback_data=f'show_cars:{page}:{page_list}')],
            [InlineKeyboardButton(text='В главное меню ◀️', callback_data='menu')]
        ]
    )

    if car_age['year'] < 2 or (car_age['year'] == 2 and car_age['month'] + 8 < 12):
        kb.inline_keyboard.insert(
            0,
            [InlineKeyboardButton(text='Рассчитать как авто 3-5 лет ❔', callback_data='calc_encar_like_old')]

        )

    return kb


def create_statement_2(car_id: int, car_age: dict):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Оставить заявку 🔥', callback_data=f'create_statement:{car_id}')],
            [InlineKeyboardButton(text='Новый расчет 🔙', callback_data='calc_link_encar')],
            [InlineKeyboardButton(text='В главное меню ◀️', callback_data='menu')]
        ]
    )

    if car_age['year'] < 2 or (car_age['year'] == 2 and car_age['month'] + 8 < 12):
        kb.inline_keyboard.insert(
            0,
            [InlineKeyboardButton(text='Рассчитать как авто 3-5 лет ❔', callback_data='calc_link_encar_like_old')]

        )

    return kb


def tracking_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='➕ Добавить отслеживание', callback_data='add_tracking')],
            [InlineKeyboardButton(text='Текущие отслеживания', callback_data='my_tracking:0')],
            [InlineKeyboardButton(text='Назад 🔙', callback_data='menu')]
        ]
    )


async def show_my_tracking_list(tracking_list: list[Tracking], tracking_count: int, page: int, session: AsyncSession):
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for track in tracking_list:
        brand_repo = BrandRepository(session)
        model_repo = ModelRepository(session)
        generation_repo = GenerationRepository(session)
        modification_repo = ModificationRepository(session)
        configuration_repo = ConfigurationRepository(session)

        configuration_name = await configuration_repo.get_configuration_name(track.configuration_id)

        modification_id = await configuration_repo.get_modification_id(track.configuration_id)
        modification_name = await modification_repo.get_modification_name(modification_id)

        generation_id = await modification_repo.get_generation_id(modification_id)
        generation_name = await generation_repo.get_generation_name(generation_id)

        model_id = await generation_repo.get_model_id(generation_id)

        brand_id = await model_repo.get_brand_id(model_id)
        brand_name = await brand_repo.get_brand_name(brand_id)

        text = f'{brand_name} {generation_name} {modification_name} {configuration_name}'

        kb.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=translator(text),
                    callback_data=f'show_my_track:{track.id}'
                )
            ]
        )

    pgn_btn = []

    if page != 0:
        pgn_btn.append(InlineKeyboardButton(
            text='⬅️ Назад',
            callback_data=f'my_tracking:{page - 1}')
        )

    if tracking_count > (page + 1) * 10:
        pgn_btn.append(InlineKeyboardButton(
            text='Далее ➡️',
            callback_data=f'my_tracking:{page + 1}')
        )

    if pgn_btn:
        kb.inline_keyboard.append(pgn_btn)

    kb.inline_keyboard.append(
        [InlineKeyboardButton(text='К предыдущему пункту ◀️', callback_data='tracking_menu')]
    )

    return kb


def show_track(track_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Удалить отслеживание', callback_data=f'delete_tracking:{track_id}')],
            [InlineKeyboardButton(text='Назад 🔙', callback_data='my_tracking:0')]
        ]
    )


def back(callback_data: str, text: str = 'Назад 🔙'):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, callback_data=callback_data)]
        ]
    )


def uploading_users():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Выгрузить пользователей', callback_data='uploading_users')]
        ]
    )


def new_car(car_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Оставить заявку', callback_data=f'create_statement:{car_id}')],
            [InlineKeyboardButton(text='◀️ Главное меню', callback_data='menu')]
        ]
    )


def cancel():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel')]
        ]
    )


def mailing_confirm():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='✅ Да', callback_data='mailing_confirm'),
                InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel')
            ]
        ]
    )
