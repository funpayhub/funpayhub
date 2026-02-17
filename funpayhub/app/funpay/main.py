from __future__ import annotations

import time
import asyncio
from typing import TYPE_CHECKING, Any, ParamSpec
from io import BytesIO
from collections import Counter
from collections.abc import Callable, Awaitable

from funpaybotengine import Bot, Dispatcher
from funpaybotengine.types import Message, Category
from funpaybotengine.client import Response, AioHttpSession
from funpaybotengine.methods import FunPayMethod, MethodReturnType
from funpaybotengine.exceptions import (
    FunPayServerError,
    UnauthorizedError,
    FunPayBotEngineError,
    RateLimitExceededError,
    BotUnauthenticatedError,
)
from funpaybotengine.types.pages import ProfilePage
from funpaybotengine.runner.config import RunnerConfig

from funpayhub.loggers import main as logger

from funpayhub.lib.exceptions import TranslatableException
from funpayhub.lib.translater import _en
from funpayhub.lib.hub.text_formatters import Image, FormattersRegistry

from funpayhub.app.funpay import middlewares as mdwr
from funpayhub.app.formatters import CATEGORIES_LIST, FORMATTERS_LIST
from funpayhub.app.dispatching import FunPayStartEvent, OffersRaisedEvent
from funpayhub.app.funpay.routers import ALL_ROUTERS
from funpayhub.app.first_response_cache import FirstResponseCache
from funpayhub.app.funpay.offers_raiser import OffersRaiser
from funpayhub.app.utils.get_profile_categories import get_profile_raisable_categories


if TYPE_CHECKING:
    from funpayhub.lib.hub.text_formatters import MessagesStack

    from funpayhub.app.main import FunPayHub
    from funpayhub.app.workflow_data import WorkflowData


P = ParamSpec('P')


class HubSession(AioHttpSession):
    def __init__(
        self,
        proxy: str | None = None,
        default_headers: dict[str, str] | None = None,
    ):
        super().__init__(proxy, default_headers)
        self._first_request = 0
        self._counter = Counter()

    async def make_request(
        self,
        method: FunPayMethod[MethodReturnType],
        bot: Bot,
        timeout: float | None = None,
        skip_session_cookies: bool = False,
    ) -> Response[MethodReturnType]:
        request_time = time.time()
        if not self._first_request:
            self._first_request = request_time
        self._counter.update([method.url])

        result = await super().make_request(method, bot, timeout, skip_session_cookies)
        return result

    @property
    def counter(self) -> Counter:
        return self._counter

    @property
    def first_request_timestamp(self) -> float:
        return self._first_request


class FunPay:
    def __init__(
        self,
        hub: FunPayHub,
        bot_token: str,
        proxy: str | None = None,
        headers: dict[str, str] | None = None,
        workflow_data: WorkflowData | None = None,
        runner_config: RunnerConfig | None = None,
    ):
        workflow_data = workflow_data if workflow_data is not None else {}

        self._hub = hub

        self._text_formatters = FormattersRegistry(workflow_data=workflow_data)
        for c in CATEGORIES_LIST:
            self._text_formatters.add_category(c)
        for i in FORMATTERS_LIST:
            self._text_formatters.add_formatter(i)

        self._session = HubSession(proxy=proxy, default_headers=headers)
        self._bot = Bot(golden_key=bot_token, session=self._session)

        self._profile_page: ProfilePage | None = None
        self._offers_raiser = OffersRaiser(self._bot)
        self._dispatcher = Dispatcher(workflow_data=workflow_data)

        self._sending_message_lock = asyncio.Lock()
        self._manually_sent_messages: set[int] = set()
        self._first_response_cache = FirstResponseCache('storage/first_response_cache.json')
        self._authenticated = False
        self._runner_config = runner_config if runner_config is not None else RunnerConfig()
        self.setup_dispatcher()

    async def start(self) -> None:
        self._authenticated = False
        try:
            await self._init_bot_engine()
        except:
            return
        self._authenticated = True
        await self._bot.listen_events(self._dispatcher, config=self._runner_config)

    async def _init_bot_engine(self) -> None:
        exception: FunPayBotEngineError | None = None
        for i in range(10):
            logger.info(_en('Trying to make a first request to FunPay...'))
            try:
                await self._bot.update()
                await self.profile(update=True)
                asyncio.create_task(self.hub.dispatcher.event_entry(FunPayStartEvent()))
                return
            except (BotUnauthenticatedError, UnauthorizedError) as e:
                logger.error(
                    _en(
                        'An error occurred while making first request to FunPay: unauthenticated.',
                    ),
                )
                exception = e
                break

            except (RateLimitExceededError, FunPayServerError) as e:
                if isinstance(e, RateLimitExceededError):
                    logger.warning(
                        _en(
                            'An error occurred while making first request to FunPay: '
                            'rate limit exceeded. Retrying in 5 seconds.',
                        ),
                    )
                else:
                    logger.warning(
                        _en(
                            'An error occurred while making first request to FunPay: '
                            'FunPay server error. Retrying in 5 seconds.',
                        ),
                    )

                await asyncio.sleep(5)
                exception = e
            except Exception as e:
                logger.error(
                    _en('An error occurred while making first request to FunPay.'),
                    exc_info=e,
                )
                exception = e
                break

        logger.error(_en('Failed to make first request to FunPay.'))
        await self.hub.dispatcher.event_entry(FunPayStartEvent(error=exception))
        raise exception

    def setup_dispatcher(self) -> None:
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

    async def send_messages_stack(
        self,
        stack: MessagesStack,
        chat_id: int | str,
        keep_chat_unread: bool = False,
        automatic_message: bool = True,
        attempts: int = 3,
    ) -> None:
        for entry in stack.entries:
            if isinstance(entry, str):
                await self.send_message(
                    chat_id=chat_id,
                    text=entry,
                    keep_chat_unread=keep_chat_unread,
                    automatic_message=automatic_message,
                    attempts=attempts,
                )
            elif isinstance(entry, Image):
                await self.send_message(
                    chat_id=chat_id,
                    image=entry.id or entry.path,
                    keep_chat_unread=keep_chat_unread,
                    automatic_message=automatic_message,
                    attempts=attempts,
                )

    async def send_message(
        self,
        chat_id: int | str,
        text: str | None = None,
        image: str | BytesIO | int | None = None,
        enforce_whitespaces: bool = True,
        keep_chat_unread: bool = False,
        automatic_message: bool = True,
        attempts: int = 3,
    ) -> Message | None:
        """
        Обёртка над funpaybotegine.Bot.send_message.
        """
        while attempts:
            attempts -= 1
            try:
                result = await self.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    image=image,
                    enforce_whitespaces=enforce_whitespaces,
                    keep_chat_unread=keep_chat_unread,
                )
                if not automatic_message:
                    self._manually_sent_messages.add(result.id)
                return result
            except RateLimitExceededError:
                await asyncio.sleep(3)
            except (BotUnauthenticatedError, UnauthorizedError) as e:
                raise TranslatableException(_en('Unable to send message.')) from e
            except Exception:
                logger.error(_en('Unable to send message to %s.'), chat_id, exc_info=True)

        raise TranslatableException(
            _en('Unable to send message to %s. Attempts exceeded.'),
            chat_id,
        )

    def is_manual_message(self, message_id: int) -> bool:
        """
        Проверяет, было ли сообщение отправлено вручную через FunPayHub.
        """
        return message_id in self._manually_sent_messages

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

    @property
    def authenticated(self) -> bool:
        return self._authenticated

    @property
    def session(self) -> HubSession:
        return self._session

    @property
    def first_response_cache(self) -> FirstResponseCache:
        return self._first_response_cache
