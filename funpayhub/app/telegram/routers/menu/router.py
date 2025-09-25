from __future__ import annotations

from aiogram import Router
from .pagination import router as pagination_router


router = Router(name='properties_menu_router')
router.include_router(pagination_router)