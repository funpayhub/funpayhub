from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, ParamSpec
from collections.abc import Callable, Awaitable

from funpaybotengine import Bot, Dispatcher
from funpaybotengine.types import Category
from funpaybotengine.types.pages import ProfilePage

from funpayhub.app.funpay import middlewares as mdwr
from funpayhub.app.formatters import CATEGORIES_LIST, FORMATTERS_LIST
from funpayhub.app.dispatching import FunPayStartEvent, OffersRaisedEvent
from funpayhub.app.funpay.routers import ALL_ROUTERS
from funpayhub.lib.hub.text_formatters import FormattersRegistry
from funpayhub.app.funpay.offers_raiser import OffersRaiser
from funpayhub.app.utils.get_profile_categories import get_profile_raisable_categories
from funpaybotengine.exceptions import BotUnauthenticatedError, UnauthorizedError, RateLimitExceededError, FunPayServerError
from loggers import main as logger


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub


P = ParamSpec('P')


class FunPay:
    def __init__(
        self,
        hub: FunPayHub,
        bot_token: str,
        proxy: str | None = None,
        headers: dict[str, str] | None = None,
        workflow_data: dict | None = None,
    ):
        workflow_data = workflow_data if workflow_data is not None else {}

        self._hub = hub

        self._text_formatters = FormattersRegistry()
        for c in CATEGORIES_LIST:
            self._text_formatters.add_category(c)
        for i in FORMATTERS_LIST:
            self._text_formatters.add_formatter(i)

        self._bot = Bot(golden_key=bot_token, proxy=proxy, default_headers=headers)

        self._profile_page: ProfilePage | None = None
        self._offers_raiser = OffersRaiser(self._bot)
        self._dispatcher = Dispatcher(workflow_data=workflow_data)
        self.setup_dispatcher()

    async def start(self):
        try:
            await self._init_bot_engine()
        except:
            return
        await self._bot.listen_events(self._dispatcher)

    async def _init_bot_engine(self):
        exception = None
        for i in range(10):
            logger.info('Trying to make a first request to FunPay...')
            try:
                await self._bot.update()
                await self.profile(update=True)
                asyncio.create_task(self.hub.dispatcher.event_entry(FunPayStartEvent()))
                return
            except (BotUnauthenticatedError, UnauthorizedError) as e:
                logger.error(
                    'An error occurred while making first request to FunPay: unauthenticated.',
                )
                exception = e
                break

            except (RateLimitExceededError, FunPayServerError) as e:
                if isinstance(e, RateLimitExceededError):
                    logger.warning(
                        'An error occurred while making first request to FunPay: '
                        'rate limit exceeded. Retrying in 5 seconds.',
                    )
                else:
                    logger.warning(
                        'An error occurred while making first request to FunPay: '
                        'FunPay server error. Retrying in 5 seconds.'
                    )

                await asyncio.sleep(5)
                exception = e
            except Exception as e:
                logger.error(
                    'An error occurred while making first request to FunPay.',
                    exc_info=e
                )
                exception = e

        logger.error('Failed to make first request to FunPay.')
        await self.hub.dispatcher.event_entry(FunPayStartEvent(error=exception))
        raise exception

    def setup_dispatcher(self):
        self.dispatcher.on_new_message.outer_middleware.register_middleware(
            mdwr.log_new_message_middleware,
        )
        self._dispatcher.connect_routers(*ALL_ROUTERS)

    async def profile(self, update: bool = False) -> ProfilePage:
        if not self._profile_page or update:
            if not self._bot.initialized:
                await self._bot.update()
            self._profile_page = await self._bot.get_profile_page(self._bot.userid)
        return self._profile_page

    async def start_raising_profile_offers(self) -> None:
        categories = await get_profile_raisable_categories(await self.profile(), self.bot)
        for category_id in categories:
            await self.offers_raiser.start_raising_loop(category_id, on_raise=self._on_raise)

    async def stop_raising_profile_offers(self) -> None:
        await self.offers_raiser.stop_all_raising_loops()

    async def _on_raise(self, category: Category) -> None:
        event = OffersRaisedEvent(category=category)
        asyncio.create_task(self.hub.dispatcher.event_entry(event))

    async def try_method[P, R](
        self,
        method: Callable[P, Awaitable[R]],
        *args: Any,
        raise_exceptions: tuple[type[Exception], ...] = (),
        attempts: int = 3,
        delay: float = 1,
        **kwargs: Any,
    ) -> R:
        if attempts <= 0:
            raise ValueError(f'Attempts amount must be greater than zero, got {attempts}.')

        while attempts:
            try:
                return await method(*args, **kwargs)
            except (
                Exception
            ) as e:  # todo: method.execute should raise SomeFunPayBotEngineError from e
                for i in raise_exceptions:
                    if isinstance(e, i):
                        raise
                await asyncio.sleep(delay)
                attempts -= 1
                if not attempts:
                    raise
        else:
            raise

    @property
    def hub(self) -> FunPayHub:
        return self._hub

    @property
    def text_formatters(self) -> FormattersRegistry:
        return self._text_formatters

    @property
    def bot(self) -> Bot:
        return self._bot

    @property
    def dispatcher(self) -> Dispatcher:
        return self._dispatcher

    @property
    def offers_raiser(self) -> OffersRaiser:
        return self._offers_raiser
