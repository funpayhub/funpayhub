from __future__ import annotations


__all__ = [
    'FunPayComponent',
]

from funpaybotengine import Bot, Router, Dispatcher
from hubplatform.app import HubPlatformApp
from hubplatform.app.context import AppContext
from hubplatform.app.app_component import HubPlatformAppComponent

from .session import FPBESession
from .properties import FunPayProperties


class FunPayComponent(HubPlatformAppComponent):
    def __init__(self, properties: FunPayProperties) -> None:
        super().__init__()
        self._properties = properties
        self._session = FPBESession()
        self._bot = Bot(golden_key='', session=self._session)
        self._router = Router(name='funpayhub.root')
        self._dispatcher = Dispatcher(self._router)

    async def setup(self, app: HubPlatformApp) -> None:
        app.properties.attach_node(self._properties)
        self._setup_context(app.app_context)
        self._dispatcher._event_context = app.app_context

    def _setup_context(self, ctx: AppContext) -> None:
        name = self.component_name
        ctx.provide(name, 'funpay', self)
        ctx.provide(name, 'funpay_props', self._properties)
        ctx.provide(name, 'funpay_bot', self._bot)
        ctx.provide(name, 'funpay_dispatcher', self._dispatcher)
        ctx.provide(name, 'funpay_router', self._router)

    async def run(self) -> None:
        await self._bot.listen_events(self._dispatcher)

    def stop(self) -> None:
        self._bot._stop_event.set()

    async def wait_stop(self) -> None:
        await self._bot._stopped_event.wait()

    @property
    def component_name(self) -> str:
        return 'funpay'

    @property
    def session(self) -> FPBESession:
        return self._session

    @property
    def bot(self) -> Bot:
        return self._bot

    @property
    def dispatcher(self) -> Dispatcher:
        return self._dispatcher

    @property
    def router(self) -> Router:
        return self._router

    @property
    def properties(self) -> FunPayProperties:
        return self._properties
