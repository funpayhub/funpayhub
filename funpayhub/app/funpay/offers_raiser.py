from __future__ import annotations

import asyncio
from contextlib import suppress

from funpaybotengine import Bot
from funpaybotengine.types import Category
from funpaybotengine.exceptions import UnauthorizedError
from funpaybotengine.exceptions.action_exceptions import RaiseOffersError
from funpaybotengine.exceptions.session_exceptions import (
    FunPayServerError,
    RateLimitExceededError,
)

from funpayhub.loggers import offers_raiser as logger


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
        self._lock = asyncio.Lock()
        self._requesting_lock = asyncio.Lock()

    async def _raising_loop(self, category: Category) -> None:
        logger.info('Цикл поднятия лотов для категории %r запущен.', category.name)
        while True:
            try:
                async with self._requesting_lock:
                    await asyncio.sleep(2)
                    await self._bot.raise_offers(category.id)
                    logger.info(
                        'Лоты категории %r успешно поднятия. Следующая попытка через %r.',
                        category.name,
                        3600,
                    )
                await asyncio.sleep(3600)
            except UnauthorizedError:
                return
            except RaiseOffersError as e:
                wait_time = e.wait_time or 1800
                logger.info(
                    'Не удалось поднять лоты категории %r: необходимо подождать %r.',
                    category.name,
                    wait_time,
                )
                await asyncio.sleep(wait_time)
                continue
            except (RateLimitExceededError, FunPayServerError) as e:
                if isinstance(e, RateLimitExceededError):
                    logger.warning(
                        'Ошибка 429 при попытке поднятия лотов категории %r.',
                        category.name,
                    )
                else:
                    logger.warning(
                        'Серверная ошибка при попытке поднятия лотов категории %r.',
                        category.name,
                    )
                await asyncio.sleep(10)
                continue
            except Exception:
                logger.error(
                    'Произошла непредвиденная ошибка при попытке поднять лоты категории %r.',
                    category.name,
                    exc_info=True,
                )
                return

    async def _wrapped_raising_loop(self, category: Category) -> None:
        try:
            await self._raising_loop(category)
        except asyncio.CancelledError:
            logger.info('Цикл поднятия лотов категории %r остановлен.', category.name)
            raise

    def _on_task_done(self, category: Category, task: asyncio.Task) -> None:
        if category.id in self._tasks and self._tasks[category.id] is task:
            del self._tasks[category.id]
            logger.debug(
                'Таска цикла поднятия лотов категории %r (%s) удалена из менеджера.',
                category.name,
                task.get_name(),
            )
        else:
            logger.debug(
                'Таска цикла поднятия лотов категории %r (%s) не была найдена в менеджере.',
                category.name,
                task.get_name(),
            )

    async def start_raising_loop(self, category_id: int) -> None:
        async with self._lock:
            if task := self._tasks.get(category_id):
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task

            category = await self._bot.storage.get_category(category_id)
            new_task = asyncio.create_task(self._wrapped_raising_loop(category))
            new_task.add_done_callback(lambda t: self._on_task_done(category, t))
            self._tasks[category_id] = new_task

    async def stop_raising_loop(self, category_id: int) -> None:
        async with self._lock:
            task = self._tasks.get(category_id)
            if task:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task

    async def stop_all_raising_loops(self) -> None:
        async with self._lock:
            tasks = list(self._tasks.values())
            for task in tasks:
                task.cancel()
            for i in tasks:
                with suppress(asyncio.CancelledError):
                    await i

    def is_raising(self, category_id: int) -> bool:
        return category_id in self._tasks
