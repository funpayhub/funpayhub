from __future__ import annotations


__all__ = [
    'FormattersContext',
    'NewMessageContext',
    'NewOrderContext',
    'DateTimeFormatter',
    'ImageFormatter',
    'OrderFormatter',
    'MessageFormatter',
    'MeFormatter',
    'GeneralFormattersCategory',
    'OrderFormattersCategory',
    'MessageFormattersCategory',
    'FORMATTERS_LIST',
    'CATEGORIES_LIST',
]

import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel
from funpaybotengine.dispatching.events import OrderEvent, NewMessageEvent

from funpayhub.lib.hub.text_formatters import Image, Formatter
from funpayhub.lib.hub.text_formatters.category import FormatterCategory


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub


_time_formats = {
    'time': '%H:%M',
    'fulltime': '%H:%M:%S',
    'date': '%d.%m',
    'fulldate': '%d.%m.%Y',
    'datetime': '%d.%m %H:%M',
    'fulldatetime': '%d.%m.%Y %H:%M:%S',
}


class FormattersContext(BaseModel): ...


class NewMessageContext(FormattersContext):
    new_message_event: NewMessageEvent


class NewOrderContext(NewMessageContext):
    order_event: OrderEvent
    goods_to_deliver: list[str]


class DateTimeFormatter(
    Formatter[FormattersContext],
    key='datetime',
    name='$formatter:datetime:name',
    description='$formatter:datetime:description',
    context_type=FormattersContext,
):
    def __init__(self, context: FormattersContext, mode: str = 'time') -> None:
        super().__init__(context)
        self.mode = mode

    async def format(self) -> str:
        now = datetime.datetime.now()

        if self.mode in _time_formats:
            return now.strftime(_time_formats[self.mode])

        return now.strftime(self.mode)


class ImageFormatter(
    Formatter[FormattersContext],
    key='image',
    name='$formatter:image:name',
    description='$formatter:image:description',
    context_type=FormattersContext,
):
    def __init__(self, context: FormattersContext, path_or_id: int | str) -> None:
        super().__init__(context)
        self.path_or_id = path_or_id

    async def format(self) -> Image:
        return Image(
            path=self.path_or_id if isinstance(self.path_or_id, str) else None,
            id=self.path_or_id if isinstance(self.path_or_id, int) else None,
        )


class OrderFormatter(
    Formatter[NewOrderContext],
    key='order',
    name='$formatter:order:name',
    description='$formatter:order:description',
    context_type=NewOrderContext,
):
    def __init__(self, context: NewOrderContext, mode: str = 'id') -> None:
        super().__init__(context)
        self.mode = mode

    async def format(self) -> str:
        order = await self.context.order_event.get_order_preview()

        if self.mode == 'id':
            return order.id or ''
        if self.mode == 'title':
            return order.title or ''
        if self.mode == 'sum':
            return str(order.total.value)
        if self.mode == 'fullsum':
            return str(order.total.value) + order.total.character
        if self.mode == 'counterparty.id':
            return str(order.counterparty.id) or ''
        if self.mode == 'counterparty.username':
            return str(order.counterparty.username) or ''

        raise ValueError(f'Unknown mode for $order formatter: {self.mode!r}')


class GoodsFormatter(
    Formatter[NewOrderContext],
    key='goods',
    name='$formatter:goods:name',
    description='$formatter:goods:description',
    context_type=NewOrderContext,
):
    def __init__(self, context: NewOrderContext, *args, **kwargs) -> None:
        super().__init__(context)

    async def format(self) -> str:
        return '\n'.join(self.context.goods_to_deliver)


class MessageFormatter(
    Formatter[NewMessageContext],
    key='message',
    name='$formatter:message:name',
    description='$formatter:message:description',
    context_type=NewMessageContext,
):
    def __init__(self, context: NewMessageContext, mode: str) -> None:
        super().__init__(context)
        self.mode = mode

    async def format(self) -> str:
        event = await self.context.new_message_event

        if self.mode == 'username':
            return event.message.sender_username or ''
        if self.mode == 'text':
            return event.message.text or ''
        if self.mode == 'chat_id':
            return event.message.chat_id or ''
        if self.mode == 'chat_name':
            return event.message.chat_name or ''
        if self.mode == 'badge_text':
            return (event.message.badge.text or '') if event.message.badge else ''

        raise ValueError(f'Unknown mode for $message formatter: {self.mode!r}')


class MeFormatter(
    Formatter[FormattersContext],
    key='me',
    name='$formatter:me:name',
    description='$formatter:me:description',
    context_type=FormattersContext,
):
    def __init__(self, context: FormattersContext, mode: str = 'username') -> None:
        super().__init__(context)
        self.mode = mode

    async def format(self, hub: FunPayHub) -> str:
        if self.mode == 'username':
            return hub.funpay.bot.username
        if self.mode == 'id':
            return str(hub.funpay.bot.userid)

        raise ValueError(f'Unknown mode for $me formatter: {self.mode!r}')


# Categories
class GeneralFormattersCategory(FormatterCategory):
    id = 'fph:general'
    name = '$formatters_categories:general:name'
    description = '$formatters_categories:general:description'
    include_formatters = {DateTimeFormatter.key, ImageFormatter.key, MeFormatter.key}


class OrderFormattersCategory(FormatterCategory):
    id = 'fph:order'
    name = '$formatters_categories:order:name'
    description = '$formatters_categories:order:description'
    include_formatters = {OrderFormatter.key, GoodsFormatter.key}


class MessageFormattersCategory(FormatterCategory):
    id = 'fph:message'
    name = '$formatters_categories:message:name'
    description = '$formatters_categories:message:description'
    include_formatters = {MessageFormatter.key}


FORMATTERS_LIST = [
    DateTimeFormatter,
    ImageFormatter,
    OrderFormatter,
    MessageFormatter,
    MeFormatter,
    GoodsFormatter,
]

CATEGORIES_LIST = [
    GeneralFormattersCategory,
    OrderFormattersCategory,
    MessageFormattersCategory,
]
