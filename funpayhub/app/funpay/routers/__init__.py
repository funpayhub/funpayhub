from __future__ import annotations

from .on_new_sale import router as on_new_sale_router
from .review_reply import review_reply_router
from .on_new_message import on_new_message_router


ALL_ROUTERS = (
    on_new_message_router,
    review_reply_router,
    on_new_sale_router,
)
