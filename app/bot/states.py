from aiogram.fsm.state import StatesGroup, State


class CarInfo(StatesGroup):
    url = State()


class CarFilter(StatesGroup):
    release_year = State()
    mileage = State()
    price = State()


class CreateStatement(StatesGroup):
    name = State()
    contact = State()


class Mailing(StatesGroup):
    message = State()
