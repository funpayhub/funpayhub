from __future__ import annotations


__all__ = ['ROUTER']


from hubplatform.telegram import Router

from .commands import router as commands_router


ROUTER = Router(name='app')
ROUTER.include_routers(
    commands_router,
)
