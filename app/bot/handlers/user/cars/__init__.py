from aiogram import Router

from .choice import router as choice_router
from .show import router as show_router

router = Router()

router.include_routers(
    choice_router,
    show_router
)
