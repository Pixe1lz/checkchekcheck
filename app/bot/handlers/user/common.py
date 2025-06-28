from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot import keyboards, functions
from services.filters import IsBlocked

router = Router()


@router.message(CommandStart(deep_link=True, deep_link_encoded=True), IsBlocked())
async def welcome(message: Message, state: FSMContext, session: AsyncSession, command: CommandObject):
    tag = command.args

    if tag:
        await state.update_data(car_id=tag)
        await functions.create_statement(message, state)
    else:
        await functions.menu(message, state, session)


@router.message(CommandStart(), IsBlocked())
async def welcome_(message: Message, state: FSMContext, session: AsyncSession):
    await functions.menu(message, state, session)


@router.callback_query(F.data == 'menu', IsBlocked())
async def welcome_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await functions.menu(callback, state, session)


@router.message(F.text == 'Главное меню', IsBlocked())
async def welcome_message(message: Message, state: FSMContext, session: AsyncSession):
    await functions.menu(message, state, session)


@router.callback_query(F.data == 'faq', IsBlocked())
async def faq(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        text=(
            f'<b>Какие авто выгодны из Кореи?</b>\n'
            f'\n'
            f'<b><u>Важно знать 1:</u></b>\n'
            f'Самые выгодные автомобили — это <b>проходные авто</b>. К таким относятся:\n'
            f' • <b>Возраст</b>: от 3 до 5 лет\n'
            f'(То есть сейчас выгодно смотреть авто <b>с апреля 2020 по апрель 2022</b>)\n'
            f' • <b>Объем двигателя</b>: до 3 литров включительно\n'
            f'\n'
            f'<b>Почему это важно?</b>\n'
            f' • Только проходные авто попадают под <b>пониженные ставки пошлины</b>\n'
            f' • До 3 литров — <b>нет коммерческого утилизационного сбора</b>\n'
            f'\n'
            f'Если объем двигателя <b>свыше 3 литров</b>, будет начислен <b>коммерческий утильсбор — 3 600 000 рублей</b>, что делает такой автомобиль <b>невыгодным</b> к растаможке.\n'
            f'\n'
            f'<b><u>Важно знать 2:</u></b>\n'
            f'<b>Кнопка 3-5 лет</b>\n'
            f'Многие наши клиенты заранее покупают авто, которое <b>ещё не стало проходным</b>, и ставят его на хранение на нашей парковке в Корее.\n'
            f'Когда наступает нужная дата — мы завозим авто в Россию по максимально выгодной таможне.\n'
            f'\n'
            f'Так как в Корее указывается дата постановки на учет, а не дата производства авто, и если вы нашли авто к примеру 2022.06 и вы хотите рассчитать такой вариант по проходной таможне — нажмите кнопку <b>«3–5 лет»</b>.'
        ),
        reply_markup=keyboards.back('menu')
    )
