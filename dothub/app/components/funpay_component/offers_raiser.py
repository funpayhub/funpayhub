from __future__ import annotations


__all__ = ['OffersRaiser', 'RaisingCategory', 'get_raisable_categories']

import time
import asyncio
from typing import TYPE_CHECKING, Any
from dataclasses import field, dataclass
from contextlib import suppress
from collections.abc import Mapping

from funpaybotengine import Bot
from hubplatform.i18n import I18nString
from funpaybotengine.types import Category, RaiseOffersResponse
from funpaybotengine.types.enums import SubcategoryType
from funpaybotengine.types.pages import ProfilePage
from funpaybotengine.exceptions.session_exceptions import (
    FunPayServerError,
    UnauthorizedError,
    RateLimitExceededError,
)

from dothub.loggers import funpay_component as logger

from .dispatching import OffersRaisedEvent


if TYPE_CHECKING:
    from eventry.asyncio import Dispatcher


REQUEST_DELAY = 2

RATE_LIMIT_DELAY = 8
SERVER_ERROR_DELAY = 10
DEFAULT_WAIT = 3600


async def get_raisable_categories(
    profile: ProfilePage,
    bot: Bot,
) -> dict[int, tuple[Category, tuple[int, ...]]]:
    """
    Returns categories that have offers on the profile, with the subcategories
    that contain those offers: ``{category_id: (category, subcategory_ids)}``.
    """
    if not profile.offers or not profile.offers.get(SubcategoryType.OFFERS):
        return {}

    subcategory_to_category = {
        subcategory.id: category
        for category in await bot.storage.get_categories()
        if category is not None
        for subcategory in category.subcategories
        if subcategory.type is SubcategoryType.OFFERS
    }

    result: dict[int, tuple[Category, tuple[int, ...]]] = {}
    for subcategory_id in profile.offers[SubcategoryType.OFFERS]:
        category = subcategory_to_category.get(subcategory_id)
        if category is None:
            continue
        _, subcategory_ids = result.get(category.id, (category, ()))
        result[category.id] = (category, (*subcategory_ids, subcategory_id))
    return result


@dataclass
class RaisingCategory:
    category: Category
    subcategory_ids: tuple[int, ...]
    task: asyncio.Task[None] | None = field(default=None, repr=False)
    next_raise_at: float | None = None
    last_raised_at: float | None = None


class OffersRaiser:
    def __init__(self, bot: Bot, dispatcher: Dispatcher) -> None:
        self._bot = bot
        self._dispatcher = dispatcher
        self._background_tasks: set[asyncio.Task[Any]] = set()
        self._categories: dict[int, RaisingCategory] = {}
        self._running = False
        self._modifying_lock = asyncio.Lock()
        self._requesting_lock = asyncio.Lock()

    @property
    def running(self) -> bool:
        return self._running

    @property
    def categories(self) -> Mapping[int, RaisingCategory]:
        return self._categories

    def is_raising(self, category_id: int) -> bool:
        return category_id in self._categories

    async def start(self, profile: ProfilePage) -> None:
        async with self._modifying_lock:
            self._running = True
            logger.info(I18nString('Offers raiser has been started.'))
            await self._sync(profile)

    async def update(self, profile: ProfilePage) -> None:
        async with self._modifying_lock:
            if self._running:
                await self._sync(profile)

    async def stop(self) -> None:
        async with self._modifying_lock:
            if not self._running:
                return
            self._running = False
            await self._stop_loops(*self._categories)
            logger.info(I18nString('Offers raiser has been stopped.'))

    async def _sync(self, profile: ProfilePage) -> None:
        raisable = await get_raisable_categories(profile, self._bot)

        to_stop = [
            category_id
            for category_id, state in self._categories.items()
            if category_id not in raisable
            or set(state.subcategory_ids) != set(raisable[category_id][1])
        ]
        await self._stop_loops(*to_stop)

        for category_id, (category, subcategory_ids) in raisable.items():
            if category_id in self._categories:
                continue
            state = RaisingCategory(category=category, subcategory_ids=subcategory_ids)
            state.task = asyncio.create_task(
                self._raising_loop(state),
                name=f'offers_raiser:{category_id}',
            )
            self._categories[category_id] = state

    async def _stop_loops(self, *category_ids: int) -> None:
        tasks = []
        for category_id in category_ids:
            state = self._categories.pop(category_id, None)
            if state is not None and state.task is not None:
                state.task.cancel()
                tasks.append(state.task)

        for task in tasks:
            with suppress(asyncio.CancelledError):
                await task

    async def _raise_until_complete(self, state: RaisingCategory) -> RaiseOffersResponse:
        while True:
            try:
                await asyncio.sleep(REQUEST_DELAY)
                return await self._bot.raise_offers(state.category.id, *state.subcategory_ids)
            except RateLimitExceededError:
                logger.warning(
                    I18nString(
                        'A 429 error occurred while raising offers of category %s. '
                        'Waiting for %d seconds.',
                    ),
                    state.category.full_name,
                    RATE_LIMIT_DELAY,
                )
                await asyncio.sleep(RATE_LIMIT_DELAY)

    async def _raising_loop(self, state: RaisingCategory) -> None:
        name = state.category.full_name
        logger.info(I18nString('Offers raising loop for category %s has been started.'), name)
        try:
            while True:
                state.next_raise_at = None
                try:
                    async with self._requesting_lock:
                        result = await self._raise_until_complete(state)
                except UnauthorizedError:
                    logger.error(
                        I18nString('Unable to raise offers of category %s: not authorized.'),
                        name,
                    )
                    return
                except FunPayServerError:
                    logger.warning(
                        I18nString('A server error occurred while raising offers of category %s.'),
                        name,
                    )
                    state.next_raise_at = time.time() + SERVER_ERROR_DELAY
                    await asyncio.sleep(SERVER_ERROR_DELAY)
                    continue
                except Exception:
                    logger.error(
                        I18nString(
                            'An unexpected error occurred while raising offers of category %s.',
                        ),
                        name,
                        exc_info=True,
                    )
                    return

                wait = (result.wait if result.wait > 0 else DEFAULT_WAIT) + 1
                state.next_raise_at = time.time() + wait
                if not result.error:
                    state.last_raised_at = time.time()
                    logger.info(
                        I18nString('Offers of category %s have been raised. Next try in %d.'),
                        name,
                        wait,
                    )
                    self._propagate_raised_event(state)
                else:
                    logger.info(
                        I18nString('Unable to raise offers of category %s: need to wait for %d.'),
                        name,
                        wait,
                    )

                await asyncio.sleep(wait)
        except asyncio.CancelledError:
            logger.info(I18nString('Offers raising loop for category %s has been stopped.'), name)
            raise
        finally:
            if self._categories.get(state.category.id) is state:
                del self._categories[state.category.id]

    def _propagate_raised_event(self, state: RaisingCategory) -> None:
        event = OffersRaisedEvent(
            category=state.category,
            subcategory_ids=state.subcategory_ids,
            next_raise_at=state.next_raise_at,
        )
        task = asyncio.create_task(
            self._dispatcher.propagate_event(event),
            name=f'offers_raiser:{state.category.id}:raised_event',
        )
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
