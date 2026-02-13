from __future__ import annotations

import asyncio
from typing import Any
from functools import partial
from contextlib import suppress
from collections.abc import Callable, Awaitable

from funpaybotengine import Bot
from funpaybotengine.types import Category
from funpaybotengine.exceptions import UnauthorizedError
from funpaybotengine.exceptions.action_exceptions import RaiseOffersError
from funpaybotengine.exceptions.session_exceptions import (
    FunPayServerError,
    RateLimitExceededError,
)

from funpayhub.loggers import offers_raiser as logger

from funpayhub.lib.translater import _en


type RaiseCallback = Callable[[Category], Awaitable[Any]]


class OffersRaiser:
    """
    Менеджер автоматического поднятия лотов по категориям.

    Для каждой категории запускается отдельная асинхронная задача (task),
    выполняющая бесконечный цикл поднятия лотов с учетом серверных ограничений
    и кулдаунов FunPay.

    Архитектура работы:
    - На каждую категорию может существовать не более одной активной задачи.
    - Все HTTP-запросы на поднятие лотов выполняются через общий
      `_requesting_lock`, что фактически сериализует запросы между категориями.
    - После каждого запроса удерживается пауза, чтобы избежать избыточной
      нагрузки и срабатывания rate-limit'ов.

    Поведение цикла:
    - При успешном поднятии лотов ожидание составляет фиксированный интервал
      (обычно 1 час).
    - При ошибке `RaiseOffersError` используется время ожидания, возвращённое
      сервером (или дефолтное).
    - При серверных ошибках и превышении лимитов выполняются короткие ретраи.
    - При `UnauthorizedError` цикл немедленно завершается.
    - Любая непредвиденная ошибка завершает цикл и логируется.

    Таким образом, несмотря на наличие отдельных задач для категорий,
    поднятие лотов фактически происходит последовательно:
    пока выполняется запрос для одной категории, остальные ожидают освобождения
    блокировки.
    """

    def __init__(self, bot: Bot) -> None:
        self._tasks: dict[int, asyncio.Task] = {}
        self._bot = bot
        self._modifying_lock = asyncio.Lock()
        self._requesting_lock = asyncio.Lock()

    async def _raise_category_until_complete(self, category: Category) -> None:
        while True:
            try:
                # Искусственное замедление запроса, чтобы не превысить rate-лимиты FunPay.
                await asyncio.sleep(2)
                await self._bot.raise_offers(category.id)
                return
            except RateLimitExceededError:
                logger.warning(
                    _en(
                        'An 429 error occurred while raising offers of category %s. '
                        'Waiting for %d seconds.',
                    ),
                    category.name,
                    8,
                )
                await asyncio.sleep(8)

    async def _raising_loop(
        self,
        category: Category,
        on_raise: RaiseCallback | None = None,
    ) -> None:
        logger.info(_en('Offer raiser loop for category %s has been started.'), category.name)
        while True:
            try:
                async with self._requesting_lock:
                    await self._raise_category_until_complete(category)
                    logger.info(
                        _en('Offers of category %s has been raised. Next try in %d.'),
                        category.name,
                        3600,
                    )
                    if on_raise is not None:
                        with suppress(Exception):
                            await on_raise(category)
                await asyncio.sleep(3600)
            except UnauthorizedError:
                logger.error(
                    _en('Unable to raise offers of category %s: not authorized.'),
                    category.name,
                )
                return
            except RaiseOffersError as e:
                wait_time = e.wait_time or 1800
                logger.info(
                    _en('Unable to raise offers of category %s: need to wait for %d.'),
                    category.name,
                    wait_time,
                )
                await asyncio.sleep(wait_time)
                continue
            except FunPayServerError:
                logger.warning(
                    _en('A Server error occurred while raising offers of category %s.'),
                    category.name,
                )
                await asyncio.sleep(10)
                continue
            except Exception:
                logger.error(
                    _en('An unexpected error occurred while raising offers of category %s.'),
                    category.name,
                    exc_info=True,
                )
                return

    async def _wrapped_raising_loop(
        self,
        category: Category,
        on_raise: RaiseCallback | None,
    ) -> None:
        try:
            await self._raising_loop(category, on_raise)
        except asyncio.CancelledError:
            logger.info(_en('Offer raising loop of category %s has been stopped.'), category.name)
            raise

    def _on_task_done(self, category: Category, task: asyncio.Task) -> None:
        if category.id in self._tasks and self._tasks[category.id] is task:
            del self._tasks[category.id]
            logger.debug(
                _en('Offer raising loop task of category %s (%s) has been removed from manager.'),
                category.name,
                task.get_name(),
            )
        else:
            logger.debug(
                _en('Offer raising loop task of category %s (%s) has not been found in manager.'),
                category.name,
                task.get_name(),
            )

    async def start_raising_loop(
        self,
        category_id: int,
        on_raise: RaiseCallback | None = None,
    ) -> None:
        async with self._modifying_lock:
            if task := self._tasks.get(category_id):
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task

            category = await self._bot.storage.get_category(category_id)
            new_task = asyncio.create_task(
                self._wrapped_raising_loop(category, on_raise),
                name=f'offers_raiser:{category.id}',
            )
            new_task.add_done_callback(partial(self._on_task_done, category))
            self._tasks[category_id] = new_task

    async def stop_raising_loop(self, category_id: int) -> None:
        async with self._modifying_lock:
            task = self._tasks.get(category_id)
            if task:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task

    async def stop_all_raising_loops(self) -> None:
        async with self._modifying_lock:
            tasks = list(self._tasks.values())
            for task in tasks:
                task.cancel()
            for i in tasks:
                with suppress(asyncio.CancelledError):
                    await i

    def is_raising(self, category_id: int) -> bool:
        return category_id in self._tasks
