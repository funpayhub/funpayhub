from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from dataclasses import field, dataclass
from itertools import chain
from collections.abc import Generator

from funpaybotengine import Router
from funpaybotengine.exceptions import (
    UnauthorizedError,
    BotUnauthenticatedError,
    UnexpectedHTTPStatusError,
)
from funpaybotengine.types.enums import MessageType
from funpaybotengine.dispatching.events import NewMessageEvent, ChatChangedEvent
from funpaybotengine.types.requests.runner import CPURequestObject

from funpayhub.loggers import greetings_logger as logger

from funpayhub.lib.translater import (
    en as _en,
    translater,
)
from funpayhub.lib.hub.text_formatters import FormattersRegistry
from funpayhub.lib.hub.text_formatters.category import InCategory

from funpayhub.app.formatters import (
    NewMessageContext,
    GeneralFormattersCategory,
    MessageFormattersCategory,
)
from funpayhub.app.properties import FunPayHubProperties
from collections import defaultdict


if TYPE_CHECKING:
    from funpaybotengine import Bot as FPBot
    from funpaybotengine.runner import EventsStack
    from funpaybotengine.types.updates import RunnerResponseObject, CurrentlyViewingOfferInfo

    from funpayhub.app.funpay.main import FunPay
    from funpayhub.app.telegram.main import Telegram
    from funpayhub.app.first_response_cache import FirstResponseCache


router = Router(name='fph:on_first_message')
ru = translater.translate


@dataclass
class NewChats:
    chat_ids: set[int]
    """ID новых чатов."""

    cpu_data: dict[int, RunnerResponseObject[CurrentlyViewingOfferInfo]] = field(
        default_factory=dict,
    )
    """Данные о просмотре лотов: {chat_id: CPU}"""


class UpdateLastChats:
    def __init__(self, events_stack: EventsStack) -> None:
        logger.debug(_en('Checking new events stack.'))

        self.stack = events_stack
        self.chats: dict[int, int] = {}
        """Словарь всех изменившихся {chat_id: user_id}, где user_id - ID собеседника."""

        self.silent_chats: set[int] = set()

        current_chat_name = ...
        for event in events_stack:
            if isinstance(event, ChatChangedEvent):
                current_chat_name = event.chat_preview.username
                logger.debug(_en('ChatChangedEvent: %s'), current_chat_name)
            elif isinstance(event, NewMessageEvent):
                if event.message.sender_username == current_chat_name and event.message.sender_id:
                    logger.debug(
                        _en('New message from user %s, that matches chat name %s.'),
                        event.message.sender_id,
                        current_chat_name,
                    )
                    self.chats[event.message.chat_id] = event.message.sender_id
                elif event.message.meta.type is MessageType.NEW_ORDER:
                    self.silent_chats.add(event.message.chat_id)
                    logger.debug(
                        _en('New order in chat %s. Marking chat as silent.'),
                        current_chat_name,
                    )

        logger.debug(_en('Finished processing events stack.'))
        logger.debug(_en('Found potentially new chats: %s.'), (self.chats,))
        logger.debug(_en('Silent chats: %s.'), (self.silent_chats,))

        self.sender_id_to_chat_id = {v: k for k, v in self.chats.items()}

    async def _get_cpu_data(
        self,
        bot: FPBot,
        *user_ids: int,
        attempts: int = 3,
    ) -> dict[int, RunnerResponseObject[CurrentlyViewingOfferInfo]]:
        objects = [CPURequestObject(id=i) for i in user_ids]
        while attempts:
            try:
                attempts -= 1
                logger.debug(_en('Getting CPU data (chunk) for users %s.'), (user_ids,))
                result = await bot.runner_request(objects)
                return {k.id: v for k, v in zip(objects, result.cpu)}
            except (UnauthorizedError, BotUnauthenticatedError):
                logger.error(
                    _en(
                        'Unable to get CPU data for users %s: unauthorized. Returning empty dict.'
                    ),
                )
                return {}
            except UnexpectedHTTPStatusError as e:
                logger.error(
                    _en('Unexpected status while getting CPU data for users %s: %s.'),
                    (user_ids, e.status),
                )
                if not attempts:
                    logger.error(
                        _en(
                            'Failed to get CPU data for users %s: attempts exceeded. '
                            'Returning empty dict.'
                        ),
                        (user_ids,),
                    )
                    return {}
            except Exception:
                logger.error(
                    _en(
                        'An unexpected error occurred while getting CPU data for users %s. '
                        'Returning empty dict.'
                    ),
                    (user_ids,),
                    exc_info=True,
                )
                return {}

    async def get_cpu_data(
        self,
        bot: FPBot,
        *user_ids: int,
        attempts: int = 3,
    ) -> dict[int, RunnerResponseObject[CurrentlyViewingOfferInfo]]:
        logger.debug(_en('Getting CPU data for users %s.'), (user_ids,))
        chunks = [tuple(user_ids[i : i + 10]) for i in range(0, len(user_ids), 10)]
        data = {}
        for i in chunks:
            data |= await self._get_cpu_data(bot, *i, attempts=attempts)
        logger.debug(_en('Got CPU data for users %s.'), ([i for i in data.keys()],))
        return data

    async def gen_new_chats_obj_task(
        self,
        chat_ids: set[int],
        get_cpu: bool,
        bot: FPBot,
    ) -> NewChats:
        obj = NewChats(chat_ids=chat_ids)
        if get_cpu:
            profiles = {self.chats[i] for i in chat_ids if i not in self.silent_chats}
            cpu_data = await self.get_cpu_data(bot, *profiles)
            obj.cpu_data = {self.sender_id_to_chat_id[k]: v for k, v in cpu_data.items()}
        return obj

    async def __call__(
        self,
        bot: FPBot,
        first_response_cache: FirstResponseCache,
        properties: FunPayHubProperties,
        **kwargs,
    ):
        if not self.has_chats:
            logger.debug(_en('No potentially new chats was found. Exiting handler.'))
            return

        logger.debug(_en('Extracting new chats from potentially new chats.'))
        new_chats = await first_response_cache.get_timed_out(
            *self.total_new_chats,
            delay=properties.first_response.timeout.value,
        )
        logger.debug(_en('New chats: %s'), (new_chats,))
        if not new_chats:
            logger.debug(_en('No new chats were found. Exiting handler.'))
            return

        logger.debug(_en('Silently updating new chats, that have NewOrder messages.'))
        await first_response_cache.update(*(i for i in self.silent_chats if i in new_chats))

        logger.debug(_en('Looking for not silent new chats.'))
        not_silent_chats = {i for i in new_chats if i not in self.silent_chats}
        logger.debug(_en('Not silent new chats: %s'), (not_silent_chats,))
        if not not_silent_chats:
            logger.debug(_en('No new chats were found. Exiting handler.'))
            return

        logger.debug(_en('Creating task to generate NewChats obj.'))
        task = asyncio.create_task(
            self.gen_new_chats_obj_task(
                new_chats,
                properties.first_response.has_offer_specific,
                bot,
            ),
        )
        self.stack['greetings_task'] = task
        logger.debug(_en('Task created and attached to events stack.'))

    @property
    def total_new_chats(self) -> Generator[int, None, None]:
        return (i for i in chain(self.chats.keys(), self.silent_chats))

    @property
    def has_chats(self) -> bool:
        return bool(self.chats) or bool(self.silent_chats)


@router.on_new_events_pack()
async def update_cpu(events_stack: EventsStack, **kwargs):
    await UpdateLastChats(events_stack)(events_stack=events_stack, **kwargs)


locks: dict[str | int, asyncio.Lock] = defaultdict(asyncio.Lock)


@router.on_new_message(as_task=True)
async def on_first_message(
    event: NewMessageEvent,
    events_stack: EventsStack,
    fp: FunPay,
    properties: FunPayHubProperties,
    fp_formatters: FormattersRegistry,
    first_response_cache: FirstResponseCache,
    tg: Telegram,
):
    async with locks[event.message.chat_id]:
        if (task := events_stack.get('greetings_task')) is None:
            logger.debug(_en('No greetings task was found. Exiting handler.'))
            return

        logger.debug('Awaiting greetings task...')
        new_chats: NewChats = await task

        if event.message.chat_id not in new_chats.chat_ids:
            logger.debug(_en('Chat %s not found in new chats. Exiting handler.'), event.message.chat_id)
            return

        message = properties.first_response.text.value
        if event.message.chat_id in new_chats.cpu_data:
            logger.debug(
                _en('Chat %s found in CPU data: %s.'),
                event.message.chat_id,
                new_chats.cpu_data[event.message.chat_id].data.id,
            )
            props = properties.first_response.get_offer(
                new_chats.cpu_data[event.message.chat_id].data.id,
            )
            if props is not None:
                logger.debug(_en('Per-offer greetings props found.'))
                message = props.text.value

        if not message:
            logger.debug(_en('Greetings text is empty. Exiting handler.'))
            return

        try:
            formatted = await fp_formatters.format_text(
                text=message,
                context=NewMessageContext(new_message_event=event),
                query=InCategory(MessageFormattersCategory).or_(InCategory(GeneralFormattersCategory)),
            )
        except Exception as e:
            logger.error(_en('Greetings text formatting error.'), exc_info=True)
            tg.send_error_notification(ru('❌ Ошибка форматирования текста приветствия.'), e)
            return

        try:
            await fp.send_messages_stack(formatted, event.message.chat_id)
            await first_response_cache.update(event.message.chat_id)
        except Exception as e:
            logger.error(_en('An error occurred while responding to the 1st message.'), exc_info=True)
            tg.send_error_notification(ru('❌ Произошла ошибка при ответе на первое сообщение.'), e)
            return
