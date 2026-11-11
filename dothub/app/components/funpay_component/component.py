from __future__ import annotations


__all__ = [
    'FunPayComponent',
]

import os
from enum import Enum, auto
from types import MappingProxyType

from funpaybotengine import Bot, Router, Dispatcher
from hubplatform.app import HubPlatformApp
from hubplatform.i18n import I18nString
from hubplatform.app.context import AppContext
from funpaybotengine.types.pages import ProfilePage
from hubplatform.app.dispatching import Dispatcher as ComponentDispatcher
from hubplatform.app.app_component import HubPlatformAppComponent

from dothub.loggers import funpay_component as logger

from .session import FPBESession
from .extensions import TELEGRAM_COMPONENT_EXTENSION
from .properties import FunPayProperties
from .dispatching import (
    ComponentRouter,
    ComponentStopEvent,
    ComponentStartEvent,
    ProfileUpdatedEvent,
    FunPayComponentEvent,
)
from .expressions import setup_funpay_component_expressions
from .offers_raiser import OffersRaiser
from .routers.on_review import router as on_review_router
from .first_response_cache import FirstResponseCache
from .routers.on_new_message import router as on_new_message_router
from .component_routers.offers_raiser import (
    router as offers_raiser_router,
    on_auto_raise_toggled,
)


class FunPayComponentState(Enum):
    READY = auto()
    STOPPED = auto()
    RUNNING = auto()
    NOT_AUTHENTICATED = auto()
    GOLDEN_KEY_CHECK_FAILED = auto()


class FunPayComponent(HubPlatformAppComponent):
    def __init__(
        self,
        properties: FunPayProperties,
        *,
        first_response_cache: FirstResponseCache | None = None,
    ) -> None:
        super().__init__()
        self._properties = properties
        self._session = FPBESession(
            proxy=os.environ.get(
                'DOTHUB_FUNPAY_PROXY',
                self._properties.bot_properties.proxy.value or None,
            ),
        )
        self._bot = Bot(
            golden_key=os.environ.get(
                'DOTHUB_FUNPAY_GOLDENKEY',
                self._properties.bot_properties.golden_key.value,
            ),
            session=self._session,
        )
        self._router = Router(name='app:funpay_component:root')
        self._dispatcher = Dispatcher(self._router)
        self._state = FunPayComponentState.STOPPED
        self._first_response_cache = (
            first_response_cache
            if first_response_cache is not None
            else FirstResponseCache('storage/funpay_component/first_response_cache.db')
        )
        self._profile: ProfilePage | None = None
        self._component_router = ComponentRouter(name='app:funpay_component:component_root')
        self._component_dispatcher = ComponentDispatcher(router=self._component_router)
        self._offers_raiser = OffersRaiser(self._bot, self._component_dispatcher)

        self._router.attach_router(on_new_message_router)
        self._router.attach_router(on_review_router)
        self._component_router.attach_router(offers_raiser_router)

    async def setup(self, app: HubPlatformApp) -> None:
        logger.info(I18nString('Setting up component...'))
        logger.info(I18nString('Setting up properties...'))
        app.properties.attach_node(self._properties)

        logger.info(I18nString('Loading first response cache...'))
        await self._first_response_cache.load()

        logger.info(I18nString('Setting up context...'))
        self._setup_context(app.app_context)
        self._dispatcher._event_context = app.app_context
        self._dispatcher._event_context_proxy = MappingProxyType(self._dispatcher._event_context)
        self._component_dispatcher._event_context = app.app_context
        self._component_dispatcher._event_context_proxy = MappingProxyType(
            self._component_dispatcher._event_context,
        )

        logger.info(I18nString('Setting up app event handlers...'))
        app.router.on_parameter_value_changed(
            lambda parameter, funpay_props: parameter is funpay_props.auto_raise,
            name='app:funpay_component:toggle_auto_raise',
        )(on_auto_raise_toggled)

        logger.info(I18nString('Setting up expressions...'))
        setup_funpay_component_expressions(app.expressions_manager)

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
        self._state = FunPayComponentState.READY

    def _setup_context(self, ctx: AppContext) -> None:
        name = self.component_name
        ctx.provide(name, 'funpay', self)
        ctx.provide(name, 'funpay_component', self)
        ctx.provide(name, 'funpay_props', self._properties)
        ctx.provide(name, 'funpay_bot', self._bot)
        ctx.provide(name, 'funpay_dispatcher', self._dispatcher)
        ctx.provide(name, 'funpay_router', self._router)
        ctx.provide(name, 'first_response_cache', self._first_response_cache)
        ctx.provide(name, 'funpay_component_router', self._component_router)
        ctx.provide(name, 'funpay_component_dispatcher', self._component_dispatcher)
        ctx.provide(name, 'offers_raiser', self._offers_raiser)

    async def run(self) -> None:
        if self._state is not FunPayComponentState.READY:
            logger.warning(I18nString('Cannot start FunPay component: not ready.'))
            return

        self._state = FunPayComponentState.RUNNING
        await self.propagate_event(ComponentStartEvent())
        try:
            await self._bot.listen_events(self._dispatcher)
        finally:
            await self.propagate_event(ComponentStopEvent())
            self._state = FunPayComponentState.READY

    def stop(self) -> None:
        self._bot._stop_event.set()

    async def wait_stop(self) -> None:
        await self._bot._stopped_event.wait()

    async def profile(self, update: bool = False, propagate_event: bool = True) -> ProfilePage:
        """
        Returns the cached profile page, fetching it if there is none or ``update`` is set.

        :param propagate_event: propagate ``ProfileUpdatedEvent`` if the profile was fetched.
        """
        if self._profile is not None and not update:
            return self._profile

        if not self._bot.initialized:
            await self._bot.update()
        self._profile = await self._bot.get_profile_page(self._bot.userid)
        if propagate_event:
            await self.propagate_event(ProfileUpdatedEvent(profile=self._profile))
        return self._profile

    async def propagate_event(self, event: FunPayComponentEvent) -> None:
        """Propagates a component event through the component router."""
        await self._component_dispatcher.propagate_event(event)

    @property
    def state(self) -> FunPayComponentState:
        return self._state

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

    @property
    def first_response_cache(self) -> FirstResponseCache:
        return self._first_response_cache

    @property
    def component_router(self) -> ComponentRouter:
        return self._component_router

    @property
    def component_dispatcher(self) -> ComponentDispatcher:
        return self._component_dispatcher

    @property
    def offers_raiser(self) -> OffersRaiser:
        return self._offers_raiser

    async def is_sent_through_app(self, message_id: int) -> bool:
        return False  # todo

    async def mark_message_as_sent_through_app(self, *message_id: int) -> None: ...

    async def unmark_message_as_sent_through_app(self, *message_id: int) -> None: ...

    async def is_automatic_message(self, message_id: int) -> bool:
        return False  # todo

    async def mark_message_as_automatic(self, *message_id: int) -> None: ...

    async def unmark_message_as_automatic(self, *message_id: int) -> None: ...
