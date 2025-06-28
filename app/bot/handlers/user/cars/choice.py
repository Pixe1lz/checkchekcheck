import re

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot import keyboards, functions
from bot.states import CarFilter
from services.filters import IsBlocked
from database.repository import generation, modification, configuration

router = Router()


@router.callback_query(F.data == 'choice_car', IsBlocked())
async def choice_car(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        text='Выберите формат расчета/подбора',
        reply_markup=keyboards.choice_format()
    )


@router.callback_query(F.data.startswith('choice_brand:'), IsBlocked())
async def choice_brand(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    page = int(callback.data.split(':')[-1])

    data = await state.get_data()
    await state.clear()
    if data.get('is_tracking'):
        await state.update_data(is_tracking=True)

    await functions.show_brands(callback, state, page, session)


@router.callback_query(F.data.startswith('choice_model:'), IsBlocked())
async def choice_model(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Вывод моделей выбранного бренда из списка"""

    _, brand_id, page = callback.data.split(':')
    brand_id, page = int(brand_id), int(page)
    await functions.show_models(callback, brand_id, page, session)
    await state.update_data(brand_id=brand_id)


@router.callback_query(F.data.startswith('choice_generation:'), IsBlocked())
async def choice_generation(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Вывод поколений выбранной модели автомобиля"""

    model_id = int(callback.data.split(':')[-1])

    generation_repo = generation.GenerationRepository(session)
    generation_info = await generation_repo.get_generations(model_id)

    data = await state.get_data()

    await callback.message.delete()
    await callback.message.answer(
        text='Выберите поколение автомобиля',
        reply_markup=keyboards.show_generation(data['brand_id'], generation_info)
    )

    await state.update_data(model_id=model_id)


@router.callback_query(F.data.startswith('choice_modification:'), IsBlocked())
async def choice_modification(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Вывод модификации выбранного поколения"""

    generation_id = int(callback.data.split(':')[-1])

    modification_repo = modification.ModificationRepository(session)
    modification_info = await modification_repo.get_modifications(generation_id)

    data = await state.get_data()

    await callback.message.delete()
    await callback.message.answer(
        text='Выберите модификацию автомобиля',
        reply_markup=keyboards.show_modification(data['model_id'], modification_info)
    )

    await state.update_data(generation_id=generation_id)


@router.callback_query(F.data.startswith('choice_configuration'), IsBlocked())
async def choice_configuration(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Вывод конфигурации выбранного модификации"""

    modification_id = int(callback.data.split(':')[-1])

    configuration_repo = configuration.ConfigurationRepository(session)
    configuration_info = await configuration_repo.get_configurations(modification_id)

    data = await state.get_data()

    await callback.message.delete()
    await callback.message.answer(
        text='Выберите конфигурацию автомобиля',
        reply_markup=keyboards.show_configuration(data['generation_id'], configuration_info)
    )

    await state.update_data(modification_id=modification_id)


@router.callback_query(F.data.startswith('pre_check_auto:'), IsBlocked())
async def pre_check_auto(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    configuration_id = int(callback.data.split(':')[-1])

    await callback.message.delete()
    await state.update_data(configuration_id=configuration_id)
    await functions.show_pre_check_auto(callback, state, session)


@router.callback_query(F.data == 'add_release_year', IsBlocked())
async def add_release_year(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        text=(
            "Введите желаемый год выпуска авто (только число или диапозон).\n"
            "Например, '2021' или '2021-2023'\n"
            "<i>от 1980 до 2025</i>"
        )
    )
    await state.set_state(CarFilter.release_year)


@router.message(F.text, CarFilter.release_year, IsBlocked())
async def release_year_validate(message: Message, state: FSMContext, session: AsyncSession):
    pattern = r'^(?:(19[89]\d|20[0-1]\d|202[0-5])|((19[89]\d|20[0-1]\d|202[0-5])-(19[89]\d|20[0-1]\d|202[0-5])))$'
    if not re.fullmatch(pattern, message.text):
        return await message.answer('Неверный формат года')

    if '-' in message.text:
        start, end = map(int, message.text.split('-'))
        if start > end:
            return await message.answer('Неверный формат диапазона года')

    await state.update_data(release_year=message.text)
    await functions.show_pre_check_auto(message, state, session)


@router.callback_query(F.data == 'add_mileage', IsBlocked())
async def add_mileage(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        text=(
            'Введите желаемый пробег автомобиля в км(только число или диапозон)\n'
            '\n'
            'Например <b>10000</b> (поиск будет ДО 10 000)\n'
            '\n'
            'Либо же <b>10000-80000</b> (поиск будет ОТ 10 000 ДО 80 000 км)\n'
            '\n'
            '<i>(Лимиты: от 0 до 200 000)</i>'
        )
    )
    await state.set_state(CarFilter.mileage)


@router.message(F.text, CarFilter.mileage, IsBlocked())
async def mileage_validate(message: Message, state: FSMContext, session: AsyncSession):
    pattern = r'^(?:(0|200000|([1-9]\d{0,4}|1\d{5}|200000))|((0|200000|([1-9]\d{0,4}|1\d{5}|200000))-(0|200000|([1-9]\d{0,4}|1\d{5}|200000))))$'
    if not re.fullmatch(pattern, message.text):
        return await message.answer('Неверный формат числа')

    if '-' in message.text:
        start, end = map(int, message.text.split('-'))
        if start > end:
            return await message.answer('Неверный формат диапазона чисел')

    def format_to_10k(value: int) -> int:
        try:
            num = int(value)
        except (ValueError, TypeError):
            return 0

        if num < 10_000:
            return 0

        return (num // 10_000) * 10_000

    if '-' in message.text:
        start, end = map(int, message.text.split('-'))
        mileage = f'{format_to_10k(start)}-{format_to_10k(end)}'
    else:
        mileage = f'{format_to_10k(message.text)}'

    await state.update_data(mileage=mileage)
    await functions.show_pre_check_auto(message, state, session)


@router.callback_query(F.data == 'add_price', IsBlocked())
async def add_price(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        text=(
            'Введите желаемую цену автомобиля в рублях(только число или диапозон)\n'
            '\n'
            'Например <b>2000000</b> (поиск будет ДО 2 000 000)\n'
            '\n'
            'Либо же <b>2000000-8000000</b> (поиск будет ОТ 2 000 000 ДО 8 000 000 рублей)\n'
            '\n'
            '<i>(Лимиты: от 0 до 100 000 000)</i>'
        )
    )
    await state.set_state(CarFilter.price)


@router.message(F.text, CarFilter.price, IsBlocked())
async def price_validate(message: Message, state: FSMContext, session: AsyncSession):
    pattern = (
        r'^'
        r'(?P<single>0|100000000|[1-9]\d{0,7})'
        r'|'
        r'(?P<range>(0|100000000|[1-9]\d{0,7})-(0|100000000|[1-9]\d{0,7}))'
        r'$'
    )

    if not re.fullmatch(pattern, message.text):
        return await message.answer('Неверный формат цены')

    if '-' in message.text:
        start, end = map(int, message.text.split('-'))
        if start > end:
            return await message.answer('Неверный формат диапазона цен')

    await state.update_data(price=message.text)
    await functions.show_pre_check_auto(message, state, session)


@router.callback_query(F.data == 'confirm', IsBlocked())
async def confirm(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    try:
        cars_info = await functions.get_cards(data, 0, session)
    except KeyError:
        await callback.message.delete()
        return await callback.message.answer('<b>Бот был перезагружен. Повторите процесс повторно.</b>')

    if cars_info:
        await state.update_data(cars_info=cars_info, page=0, page_list=0)
        await callback.message.delete()
        await functions.show_cars(callback, session, data['configuration_id'], cars_info)
    else:
        await callback.answer('Произошла техническая ошибка')
