from __future__ import annotations


__all__ = [
    'FunPayComponent',
]

from enum import Enum, auto

from funpaybotengine import Bot, Router, Dispatcher
from hubplatform.app import HubPlatformApp
from hubplatform.i18n import I18nString
from hubplatform.app.context import AppContext
from funpaybotengine.types.pages import ProfilePage
from hubplatform.app.app_component import HubPlatformAppComponent

from funpayhub.loggers import funpay_component as logger

from .session import FPBESession
from .extensions import TELEGRAM_COMPONENT_EXTENSION
from .properties import FunPayProperties


class FunPayComponentState(Enum):
    READY = auto()
    STOPPED = auto()
    RUNNING = auto()
    NOT_AUTHENTICATED = auto()
    GOLDEN_KEY_CHECK_FAILED = auto()


class FunPayComponent(HubPlatformAppComponent):
    def __init__(self, properties: FunPayProperties) -> None:
        super().__init__()
        self._properties = properties
        self._session = FPBESession()
        self._bot = Bot(golden_key='', session=self._session)
        self._router = Router(name='funpayhub.root')
        self._dispatcher = Dispatcher(self._router)
        self._state = FunPayComponentState.STOPPED
        self._profile: ProfilePage | None = None

    async def setup(self, app: HubPlatformApp) -> None:
        logger.info(I18nString('Setting up %s component...'), self.component_name)
        logger.info(I18nString('Setting up %s component properties...'), self.component_name)
        app.properties.attach_node(self._properties)

        logger.info(I18nString('Setting up %s component context...'), self.component_name)
        self._setup_context(app.app_context)
        self._dispatcher._event_context = app.app_context

        logger.info(I18nString('Setting up telegram extension...'))
        app.add_component_extension('hubplatform.telegram', TELEGRAM_COMPONENT_EXTENSION)

        logger.info(I18nString('Checking golden_key...'))
        await self._check_golden_key()

    async def _check_golden_key(self) -> None:
        try:
            await self._bot.update()
        except Exception:
            logger.error(
                I18nString('An error occurred while checking golden key.'),
                exc_info=True,
            )
            self._state = FunPayComponentState.GOLDEN_KEY_CHECK_FAILED
            return

        if self._bot.userid == -1:
            logger.warning(I18nString('FunPay authentication failed: invalid golden key.'))
            self._state = FunPayComponentState.NOT_AUTHENTICATED
            return

        logger.info(I18nString('FunPay successfully authenticated!.'))
        logger.info(I18nString('User ID: %d'), self._bot.userid)
        logger.info(I18nString('User name: %s'), self._bot.username)
        logger.info(I18nString('Locale: %s'), self._bot.locale.name)
        self._statue = FunPayComponentState.READY

    def _setup_context(self, ctx: AppContext) -> None:
        name = self.component_name
        ctx.provide(name, 'funpay', self)
        ctx.provide(name, 'funpay_props', self._properties)
        ctx.provide(name, 'funpay_bot', self._bot)
        ctx.provide(name, 'funpay_dispatcher', self._dispatcher)
        ctx.provide(name, 'funpay_router', self._router)

    async def run(self) -> None:
        if self._state is not FunPayComponentState.READY:
            logger.warning(I18nString('Cannot start FunPay component: not ready.'))
            return

        await self._bot.listen_events(self._dispatcher)

    def stop(self) -> None:
        self._bot._stop_event.set()

    async def wait_stop(self) -> None:
        await self._bot._stopped_event.wait()

    async def profile(self, update: bool = False) -> ProfilePage:
        if self._profile is None or update:
            if not self._bot.initialized:
                await self._bot.update()
            self._profile = await self._bot.get_profile_page(self._bot.userid)
        return self._profile

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
