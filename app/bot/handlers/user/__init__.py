from aiogram import Router

from .common import router as common_router
from .cars import router as cars_router
from .statement import router as statement_router
from .tracking import router as tracking_router

router = Router()

router.include_routers(
    common_router,
    cars_router,
    statement_router,
    tracking_router,
)
