from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot import keyboards, functions
from config import settings
from services.filters import IsBlocked
from database.repository.tracking import TrackingRepository

router = Router()


@router.callback_query(F.data == 'tracking_menu', IsBlocked())
async def tracking_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    await callback.message.delete()
    await callback.message.answer(
        'Получайте уведомления о новых объявлений авто по вашим фильтрам',
        reply_markup=keyboards.tracking_menu()
    )


@router.callback_query(F.data == 'add_tracking', IsBlocked())
async def add_tracking(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.clear()
    await state.update_data(is_tracking=True)
    await functions.show_brands(callback, state, 0, session)


@router.callback_query(F.data == 'save_tracking', IsBlocked())
async def save_tracking(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    await state.clear()

    tracking_repo = TrackingRepository(session)

    track_info = await tracking_repo.tracking_create(
        callback.from_user.id,
        data['configuration_id'],
        data.get('release_year'),
        data.get('mileage'),
        data.get('price')
    )

    await callback.answer('Отслеживание успешно создана!')
    await tracking_menu(callback, state)

    username_text = f' @{callback.from_user.username}' if callback.from_user.username else ''

    await functions.show_track(
        settings.LOG_CHAT_ID,
        session,
        track_info.id,
        is_support=True,
        title=f'<b>Пользователь <a href="tg://user?id={callback.from_user.id}">{callback.from_user.first_name}{username_text}</a> '
              f'(ID: {callback.from_user.id}) добавил в отслеживание</b>'
    )

    await functions.activate_tracking(session, track_info.id)


@router.callback_query(F.data.startswith('my_tracking:'), IsBlocked())
async def my_tracking(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    page = int(callback.data.split(':')[1])

    await state.clear()
    tracking_repo = TrackingRepository(session)
    tracking_count = await tracking_repo.tracking_count(callback.from_user.id)
    if tracking_count:
        await functions.show_my_tracking(callback, tracking_count, session, page)
    else:
        await callback.answer('У вас нет активных отслеживаний', show_alert=True)


@router.callback_query(F.data.startswith('show_my_track:'), IsBlocked())
async def show_my_track(callback: CallbackQuery, session: AsyncSession):
    track_id = int(callback.data.split(':')[1])

    await callback.message.delete()
    await functions.show_track(callback.from_user.id, session, track_id, title='Ваши параметры:')


@router.callback_query(F.data.startswith('delete_tracking:'), IsBlocked())
async def delete_tracking(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    track_id = int(callback.data.split(':')[1])

    tracking_repo = TrackingRepository(session)
    await tracking_repo.tracking_delete(track_id)

    await callback.answer('Отслеживание успешно удалена!')

    await tracking_menu(callback, state)
