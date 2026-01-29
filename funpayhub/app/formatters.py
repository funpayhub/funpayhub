from __future__ import annotations


__all__ = [
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


class DateTimeFormatter(
    Formatter,
    key='datetime',
    name='$formatter:datetime:name',
    description='$formatter:datetime:description',
):
    def __init__(self, mode: str = 'time') -> None:
        self.mode = mode

    async def format(self) -> str:
        now = datetime.datetime.now()

        if self.mode in _time_formats:
            return now.strftime(_time_formats[self.mode])

        return now.strftime(self.mode)


class ImageFormatter(
    Formatter,
    key='image',
    name='$formatter:image:name',
    description='$formatter:image:description',
):
    def __init__(self, path_or_id: int | str) -> None:
        self.path_or_id = path_or_id

    async def format(self) -> Image:
        return Image(
            path=self.path_or_id if isinstance(self.path_or_id, str) else None,
            id=self.path_or_id if isinstance(self.path_or_id, int) else None,
        )


class OrderFormatter(
    Formatter,
    key='order',
    name='$formatter:order:name',
    description='$formatter:order:description',
):
    def __init__(self, mode: str = 'id') -> None:
        self.mode = mode

    async def format(self, event: OrderEvent) -> str:
        if not isinstance(event, OrderEvent):
            raise TypeError('$order formatter can only be used in order context.')
        order = await event.get_order_preview()

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


class MessageFormatter(
    Formatter,
    key='message',
    name='$formatter:message:name',
    description='$formatter:message:description',
):
    def __init__(self, mode: str) -> None:
        self.mode = mode

    async def format(self, event: NewMessageEvent) -> str:
        if not isinstance(event, NewMessageEvent):
            raise TypeError('$message formatter can only be used with NewMessageEvent context.')

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
    Formatter,
    key='me',
    name='$formatter:me:name',
    description='$formatter:me:description',
):
    def __init__(self, mode: str = 'username') -> None:
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
    include_formatters = {OrderFormatter.key}


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
]

CATEGORIES_LIST = [
    GeneralFormattersCategory,
    OrderFormattersCategory,
    MessageFormattersCategory,
]
