import asyncio

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from bot import keyboards, functions
from bot.states import CreateStatement
from services.filters import IsBlocked

router = Router()


@router.callback_query(F.data.startswith('create_statement:'), IsBlocked())
async def create_statement(callback: CallbackQuery, state: FSMContext):
    _, car_id = callback.data.split(':')
    await state.update_data(car_id=car_id)

    await functions.create_statement(callback, state)


@router.message(F.text, CreateStatement.name, IsBlocked())
async def name_validate(message: Message, state: FSMContext):
    await message.answer('Очень приятно! Напишите свой контакт в свободной форме (Telegram/WhatsApp/номер телефона)')
    await state.set_state(CreateStatement.contact)
    await state.update_data(statement_name=message.text)


@router.message(F.text, CreateStatement.contact, IsBlocked())
async def contact_validate(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    await message.answer('Ваша заявка принята в ближайшее время с вами свяжется менеджер')

    await asyncio.sleep(1)
    await message.answer(
        text=(
            'Выберите следующее действие:\n'
            '\n'
            '/start - перезапуск бота'
        ),
        reply_markup=keyboards.inline_menu()
    )

    car_age = data.get('car_age')
    if not car_age:
        car_info = await functions.get_car_info_url(data['car_id'])
        if car_info:
            await state.clear()

            car_age = functions.cal_car_age(
                int(str(car_info['cars']['base']['category']['yearMonth'])[:4]),
                str(car_info['cars']['base']['category']['yearMonth'])[4:]
            )

    await functions.send_notification_statement_to_admins(
        message.from_user,
        data['car_id'],
        car_age,
        data['statement_name'],
        message.text
    )
