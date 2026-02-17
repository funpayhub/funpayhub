from __future__ import annotations

from .on_review import r as on_review_router
from .on_new_sale import router as on_new_sale_router
from .on_new_message import on_new_message_router
from .on_first_message import router as on_first_message_router


ALL_ROUTERS = (
    on_new_message_router,
    on_review_router,
    on_new_sale_router,
    on_first_message_router,
)
