__all__ = [
    'DateTimeFormatter',
    'ImageFormatter',
    'UsernameFormatter',
    'OrderIdFormatter',
]

from funpayhub.lib.hub.text_formatters import Formatter, Image
from funpaybotengine.dispatching.events import NewMessageEvent, OrderEvent
import datetime


_time_formats = {
    'time': '%H:%M',
    'fulltime': '%H:%M:%S',
    'date': '%d.%m',
    'fulldate': '%d.%m.%Y',
    'datetime': '%d.%m %H:%M',
    'fulldatetime': '%d.%m.%Y %H:%M:%S'
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
    formatter=datetime_formatter
)


async def image_formatter(path_or_id: int | str) -> Image:
    return Image(
        path=path_or_id if isinstance(path_or_id, str) else None,
        id=path_or_id if isinstance(path_or_id, int) else None
    )


ImageFormatter = Formatter(
    key='image',
    name='$formatter:image:name',
    description='$formatter:image:description',
    formatter=image_formatter
)


async def username_formatter(event: NewMessageEvent | OrderEvent) -> str:
    if isinstance(event, NewMessageEvent):
        return event.message.sender_username or ''

    order_preview = await event.get_order_preview()
    return order_preview.counterparty.username or ''


UsernameFormatter = Formatter(
    key='username',
    name='$formatter:username:name',
    description='$formatter:username:description',
    formatter=username_formatter
)


async def order_id_formatter(event: OrderEvent) -> str:
    if not isinstance(event, OrderEvent):
        raise ValueError('') # todo

    order_preview = await event.get_order_preview()
    return order_preview.id


OrderIdFormatter = Formatter(
    key='id',
    name='$formatter:order_id:name',
    description='$formatter:order_id:description',
    formatter=order_id_formatter
)