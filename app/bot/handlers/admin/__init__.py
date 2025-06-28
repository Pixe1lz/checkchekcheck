from aiogram import Router

from .common import router as common_router

router = Router()

router.include_routers(
    common_router
)
