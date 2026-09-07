from __future__ import annotations

from .other import router as other_router
from .on_parameter_change import router


ROUTERS = [
    router,
    other_router,
]
