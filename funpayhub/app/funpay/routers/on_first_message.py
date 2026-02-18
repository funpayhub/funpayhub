from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import field, dataclass

from funpaybotengine import Router
from funpaybotengine.exceptions import (
    UnauthorizedError,
    BotUnauthenticatedError,
    UnexpectedHTTPStatusError,
)
from funpaybotengine.dispatching.events import NewMessageEvent, ChatChangedEvent
from funpaybotengine.types.requests.runner import CPURequestObject

from funpayhub.loggers import main as logger

from funpayhub.lib.translater import _en
from funpayhub.lib.hub.text_formatters import FormattersRegistry
from funpayhub.lib.hub.text_formatters.category import InCategory

from funpayhub.app.formatters import (
    NewMessageContext,
    GeneralFormattersCategory,
    MessageFormattersCategory,
)
from funpayhub.app.properties import FunPayHubProperties


if TYPE_CHECKING:
    from funpaybotengine import Bot as FPBot
    from funpaybotengine.runner import EventsStack
    from funpaybotengine.types.updates import RunnerResponseObject, CurrentlyViewingOfferInfo

    from funpayhub.lib.translater import Translater

    from funpayhub.app.funpay.main import FunPay
    from funpayhub.app.telegram.main import Telegram
    from funpayhub.app.first_response_cache import FirstResponseCache


router = Router(name='fph:on_first_message')


@dataclass
class NewChats:
    chat_ids: set[int]
    """ID новых чатов."""

    cpu_data: dict[int, RunnerResponseObject[CurrentlyViewingOfferInfo]] = field(
        default_factory=dict
    )
    """Данные о просмотре лотов: {chat_id: CPU}"""


LAST_CHATS: NewChats | None = None


class UpdateLastChats:
    def __init__(self, events_stack: EventsStack) -> None:
        self.chats: dict[int, int] = {}
        """Словарь всех изменившихся {chat_id: user_id}, где user_id - ID собеседника."""

        # Исключаем все чаты, в которых нет сообщения от самого собеседника
        # (а только от нас / других пользователей (поддержка))
        current_chat_name = ...
        for event in events_stack:
            if isinstance(event, ChatChangedEvent):
                current_chat_name = event.chat_preview.username
            elif isinstance(event, NewMessageEvent):
                if event.message.sender_username == current_chat_name and event.message.sender_id:
                    self.chats[event.message.chat_id] = event.message.sender_id

        self.sender_id_to_chat_id = {v: k for k, v in self.chats.items()}

    async def get_timed_out_chats(self, cache: FirstResponseCache, delay: int):
        """Возвращает список всех "новых" чатов из `self.chats`."""
        return {i for i in self.chats.keys() if await cache.is_new(i, delay)}

    async def _get_cpu_data(
        self, bot: FPBot, *user_ids: int, attempts: int = 3
    ) -> dict[int, RunnerResponseObject[CurrentlyViewingOfferInfo]]:
        objects = [CPURequestObject(id=i) for i in user_ids]
        while attempts:
            try:
                attempts -= 1
                result = await bot.runner_request(objects)
                return {k.id: v for k, v in zip(objects, result.cpu)}
            except (UnauthorizedError, BotUnauthenticatedError):
                raise
            except UnexpectedHTTPStatusError:
                if not attempts:
                    raise
        raise RuntimeError()

    async def get_cpu_data(
        self,
        bot: FPBot,
        *user_ids: int,
        attempts: int = 3,
    ) -> dict[int, RunnerResponseObject[CurrentlyViewingOfferInfo]]:
        chunks = [tuple(user_ids[i : i + 10]) for i in range(0, len(user_ids), 10)]
        data = {}
        for i in chunks:
            data |= await self._get_cpu_data(bot, *i, attempts=attempts)
        return data

    async def __call__(
        self,
        bot: FPBot,
        first_response_cache: FirstResponseCache,
        properties: FunPayHubProperties,
        **kwargs,
    ):
        global LAST_CHATS
        new_chats = await self.get_timed_out_chats(
            first_response_cache,
            properties.first_response.timeout.value,
        )

        cpu_data = {}
        if properties.first_response.has_offer_specific:
            profiles = {self.chats[i] for i in new_chats}
            cpu_data = await self.get_cpu_data(bot, *profiles)
            cpu_data = {self.sender_id_to_chat_id[k]: v for k, v in cpu_data.items()}
        data_obj = NewChats(chat_ids=new_chats, cpu_data=cpu_data)
        LAST_CHATS = data_obj


@router.on_new_events_pack()
async def update_cpu(events_stack: EventsStack, **kwargs):
    global LAST_CHATS
    LAST_CHATS = None
    await UpdateLastChats(events_stack)(events_stack=events_stack, **kwargs)


@router.on_new_message(
    lambda message: LAST_CHATS is not None and message.chat_id in LAST_CHATS.chat_ids,
)
async def on_first_message(
    event: NewMessageEvent,
    fp: FunPay,
    properties: FunPayHubProperties,
    fp_formatters: FormattersRegistry,
    first_response_cache: FirstResponseCache,
    tg: Telegram,
    translater: Translater,
):
    if not (
        await first_response_cache.is_new(
            event.message.chat_id,
            properties.first_response.timeout.value,
        )
    ):
        return
    await first_response_cache.update(event.message.chat_id)

    message = properties.first_response.text.value
    if event.message.chat_id in LAST_CHATS.cpu_data:
        props = properties.first_response.get_offer(
            LAST_CHATS.cpu_data[event.message.chat_id].data.id
        )
        if props is not None:
            message = props.text.value

    if not message:
        return

    try:
        context = NewMessageContext(new_message_event=event)
        formatted = await fp_formatters.format_text(
            text=message,
            context=context,
            query=InCategory(MessageFormattersCategory).or_(InCategory(GeneralFormattersCategory)),
        )
    except Exception as e:
        logger.error(
            _en('An error occurred while formatting text for the first message response.'),
            exc_info=True,
        )
        tg.send_error_notification(
            translater.translate(
                '❌ Произошла ошибка при форматировании текста для ответа на первое сообщение.'
            ),
            exception=e,
        )
        return

    try:
        await fp.send_messages_stack(formatted, event.message.chat_id)
    except Exception as e:
        logger.error(
            _en('An error occurred while sending the first message response.'),
            exc_info=True,
        )
        tg.send_error_notification(
            translater.translate('❌ Произошла ошибка при ответе на первое сообщение.'),
            exception=e,
        )
        return
