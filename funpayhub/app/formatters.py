from __future__ import annotations


__all__ = [
    'DateTimeFormatter',
    'ImageFormatter',
    'OrderFormatter',
    'MessageFormatter',
    'MeFormatter',
    'FORMATTERS_LIST',
]

import datetime
from typing import TYPE_CHECKING
from funpaybotengine.dispatching.events import OrderEvent, NewMessageEvent

from funpayhub.lib.hub.text_formatters import Image, Formatter

if TYPE_CHECKING:
    from funpayhub.app import FunPayHub


_time_formats = {
    'time': '%H:%M',
    'fulltime': '%H:%M:%S',
    'date': '%d.%m',
    'fulldate': '%d.%m.%Y',
    'datetime': '%d.%m %H:%M',
    'fulldatetime': '%d.%m.%Y %H:%M:%S',
}


async def datetime_formatter(mode: str = 'time') -> str:
    now = datetime.datetime.now()

    if mode in _time_formats:
        return now.strftime(_time_formats[mode])

    return now.strftime(mode)


DateTimeFormatter = Formatter(
    key='time',
    name='$formatter:datetime:name',
    description='$formatter:datetime:description',
    formatter=datetime_formatter,
)


async def image_formatter(path_or_id: int | str) -> Image:
    return Image(
        path=path_or_id if isinstance(path_or_id, str) else None,
        id=path_or_id if isinstance(path_or_id, int) else None,
    )


ImageFormatter = Formatter(
    key='image',
    name='$formatter:image:name',
    description='$formatter:image:description',
    formatter=image_formatter,
)


async def order_formatter(mode: str = 'id', event: OrderEvent | None = None) -> str:
    if not isinstance(event, OrderEvent):
        raise TypeError('$order formatter can only be used in order context.')

    order = await event.get_order_preview()

    if mode == 'id':
        return order.id or ''
    if mode == 'title':
        return order.title or ''
    if mode == 'sum':
        return str(order.total.value)
    if mode == 'fullsum':
        return str(order.total.value) + order.total.character
    if mode == 'counterparty.id':
        return str(order.counterparty.id) or ''
    if mode == 'counterparty.username':
        return str(order.counterparty.username) or ''

    raise ValueError(f'Unknown mode for $order formatter: {mode!r}')


OrderFormatter = Formatter(
    key='order',
    name='$formatter:order:name',
    description='$formatter:order:description',
    formatter=order_formatter,
)


async def message_formatter(mode, event: NewMessageEvent | None = None) -> str:
    if not isinstance(event, NewMessageEvent):
        raise TypeError('$message formatter can only be used in message context.')

    if mode == 'username':
        return event.message.sender_username or ''
    if mode == 'text':
        return event.message.text or ''
    if mode == 'chat_id':
        return event.message.chat_id or ''
    if mode == 'chat_name':
        return event.message.chat_name or ''
    if mode == 'badge_text':
        return (event.message.badge.text or '') if event.message.badge else ''

    raise ValueError(f'Unknown mode for $message formatter: {mode!r}')


MessageFormatter = Formatter(
    key='message',
    name='$formatter:message:name',
    description='$formatter:message:description',
    formatter=message_formatter,
)


async def me_formatter(mode: str = 'username', hub: FunPayHub | None = None) -> str:
    if mode == 'username':
        return hub.funpay.bot.username
    if mode == 'id':
        return str(hub.funpay.bot.userid)

    raise ValueError(f'Unknown mode for $me formatter: {mode!r}')

MeFormatter = Formatter(
    key='me',
    name='$formatter:me:name',
    description='$formatter:me:description',
    formatter=me_formatter,
)


FORMATTERS_LIST = [
    DateTimeFormatter,
    ImageFormatter,
    OrderFormatter,
    MessageFormatter,
    MeFormatter,
]
