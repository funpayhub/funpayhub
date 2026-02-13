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

import re
import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel
from funpaybotengine.dispatching.events import OrderEvent, NewMessageEvent

from funpayhub.lib.translater import _
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

NEW_LINE_RE = re.compile(r'(?<!\\)\\n')


DATETIME_DESC = _(
    'Позволяет вставить в текст текущую дату и время.\n\n'
    'Пример использования:\n'
    '<blockquote>Текущее время: $datetime</blockquote>\n'
    'Вывод:\n'
    '<blockquote>Текущее время: 12:34</blockquote>\n\n'
    'Поддерживает несколько режимом вставки:\n'
    '1. <code>time</code> (по умолчанию). Выводит текущее время в формате <code>ЧЧ:ММ</code>.\n'
    'Пример использования: <code>$datetime</code> или <code>$datetime&lt;time&gt;</code>\n'
    'Пример вывода: <code>12:34</code>\n\n'
    '2. <code>fulltime</code>. Выводит текущее время в формате <code>ЧЧ:ММ:СС</code>.\n'
    'Пример использования: <code>$datetime&lt;fulltime&gt;</code>\n'
    'Пример вывода: <code>12:34:56</code>\n\n'
    '3. <code>date</code>. Выводит текущую дату в формате <code>ДД.ММ</code>.\n'
    'Пример использования: <code>$datetime&lt;date&gt;</code>\n'
    'Пример вывода: <code>20.09</code>\n\n'
    '4. <code>fulldate</code>. Выводит текущую дату в формате <code>ДД.ММ.ГГГГ</code>.\n'
    'Пример использования: <code>$datetime&lt;fulldate&gt;</code>\n'
    'Пример вывода: <code>20.09.2002</code>\n\n'
    '5. <code>datetime</code>. Выводит текущую дату и время в формате <code>ДД.ММ ЧЧ:ММ</code>.\n'
    'Пример использования: <code>$datetime&lt;datetime&gt;</code>\n'
    'Пример вывода: <code>20.09 12:34</code>\n\n'
    '6. <code>fulldatetime</code>. Выводит текущую дату и время в формате '
    '<code>ДД.ММ.ГГГГ ЧЧ:ММ:CC</code>.\n'
    'Пример использования: <code>$datetime&lt;fulldatetime&gt;</code>\n'
    'Пример вывода: <code>20.09:2002 12:34:56</code>\n\n'
    'Так же в качестве аргумента можно передать Python <code>strftime()</code> строку.\n'
    'Подробнее: '
    '<a href="https://docs.python.org/3.13/library/datetime.html#strftime-strptime-behavior">'
    'Python strftime()</a>',
)

IMAGE_DESC = _(
    'Позволяет вставить в текст изображение.\n'
    'Имеет один обязательный параметр: путь до изображения или ID изображения.\n\n'
    'Пример использования:\n'
    '<blockquote>Вот твоя картинка: $image&lt;path/to/the/image&gt;</blockquote>\n'
    'или\n'
    '<blockquote>Вот твоя картинка: $image&lt;12345&gt;</blockquote>\n\n'
    '<b><u>Важно!</u></b>\n'
    'FunPay не может отправить и изображение, и текст одним сообщением. '
    'Потому, если вы вставляет изображение в текст, будет отправляться несколько сообщений: '
    'текст до изображения, изображение, текст после изображения.',
)

ORDER_DESC = _(
    'Позволяет вставить в текст информацию о заказе.\n'
    'Пример использования:\n'
    '<blockquote>ID заказа: $order</blockquote>\n'
    'Вывод:\n'
    '<blockquote>ID заказа: AB3C56DE</blockquote>\n\n'
    'Поддерживает несколько режимом вставки:\n'
    '1. <code>id</code> (по умолчанию). Выводит ID заказа.\n'
    'Пример использования: <code>$order</code> или <code>$order&lt;id&gt;</code>\n'
    'Пример вывода: <code>AB3C56DE</code>\n\n'
    '2. <code>title</code> (по умолчанию). Выводит краткое описание заказа.\n'
    'Пример использования: <code>$order&lt;title&gt;</code>\n'
    'Пример вывода: <code>Аккаунты какой-то игры, 10шт.</code>\n\n'
    '3. <code>sum</code> (по умолчанию). Выводит сумму заказа без указания валюты.\n'
    'Пример использования: <code>$order&lt;sum&gt;</code>\n'
    'Пример вывода: <code>1234.56</code>\n\n'
    '4. <code>fullsum</code> (по умолчанию). Выводит сумму заказа с указанием валюты.\n'
    'Пример использования: <code>$order&lt;fullsum&gt;</code>\n'
    'Пример вывода: <code>1234.56$</code>\n\n'
    '5. <code>counterparty.id</code> (по умолчанию). Выводит ID покупателя.\n'
    'Пример использования: <code>$order&lt;counterparty.id&gt;</code>\n'
    'Пример вывода: <code>16161616</code>\n\n'
    '6. <code>counterparty.username</code> (по умолчанию). Выводит имя пользователя покупателя.\n'
    'Пример использования: <code>$order&lt;counterparty.username&gt;</code>\n'
    'Пример вывода: <code>Gygabrain</code>\n\n',
)

MESSAGE_DESC = _(
    'Позволяет вставить в текст информацию о сообщении.\n'
    'Имеет один обязательный параметр: режим вставки.\n\n'
    'Поддерживает несколько режимом вставки:\n'
    '1. <code>username</code>. Вставляет имя пользователя отправителя сообщения.\n'
    'Пример использования: <code>$message&lt;username&gt;</code>\n'
    'Пример вывода: <code>Gygabrain</code>\n\n'
    '2. <code>text</code>. Вставляет текст сообщения.\n'
    'Пример использования: <code>$message&lt;text&gt;</code>\n'
    'Пример вывода: <code>Текст сообщения от Gygabrain</code>\n\n'
    '3. <code>chat_id</code>. Вставляет ID чата.\n'
    'Пример использования: <code>$message&lt;chat_id&gt;</code>\n'
    'Пример вывода: <code>123456789</code>\n\n'
    '4. <code>chat_id</code>. Вставляет название чата.n'
    'Пример использования: <code>$message&lt;chat_name&gt;</code>\n'
    'Пример вывода: <code>node-123456789-987654321</code>\n\n'
    '5. <code>badge_text</code>. Вставляет текст бейджика отправителя.n'
    'Пример использования: <code>$message&lt;badge_text&gt;</code>\n'
    'Пример вывода: <code>Поддержка</code>\n\n',
)

ME_DESC = _(
    'Позволяет вставить в текст информацию о вас.\n'
    'Пример использования:\n'
    '<blockquote>Добро пожаловать в магазин $me!</blockquote>\n'
    'Вывод:\n'
    '<blockquote>Добро пожаловать в магазин Gygabrain!</blockquote>\n\n'
    'Поддерживает несколько режимом вставки:\n'
    '1. <code>username</code> (по умолчанию). Выводит ваше имя пользователя.\n'
    'Пример использования: <code>$me</code> или <code>$me&lt;username&gt;</code>\n'
    'Пример вывода: <code>Gygabrain</code>\n\n'
    '2. <code>id</code> (по умолчанию). Выводит ваш ID.\n'
    'Пример использования: <code>$me&lt;id&gt;</code>\n'
    'Пример вывода: <code>16161616</code>\n\n',
)


class FormattersContext(BaseModel): ...


class NewMessageContext(FormattersContext):
    new_message_event: NewMessageEvent


class NewOrderContext(NewMessageContext):
    order_event: OrderEvent
    goods_to_deliver: list[str]


class DateTimeFormatter(
    Formatter[FormattersContext],
    key='datetime',
    name=_('📆 Дата и время ($datetime)'),
    description=DATETIME_DESC,
    context_type=FormattersContext,
):
    def __init__(self, context: FormattersContext, mode: str = 'time', *args, **kwargs) -> None:
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
    name=_('🖼️ Изображение ($image)'),
    description=_(IMAGE_DESC),
    context_type=FormattersContext,
):
    def __init__(self, context: FormattersContext, path_or_id: int | str, *args, **kwargs) -> None:
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
    name=_('🛍️ Информация о заказе ($order)'),
    description=ORDER_DESC,
    context_type=NewOrderContext,
):
    def __init__(self, context: NewOrderContext, mode: str = 'id', *args, **kwargs) -> None:
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
    name=_('🗳 Товары ($goods)'),
    description=_('Подставляет товары.'),
    context_type=NewOrderContext,
):
    def __init__(self, context: NewOrderContext, *args, **kwargs) -> None:
        super().__init__(context)

    async def format(self) -> str:
        return NEW_LINE_RE.sub('\n', '\n'.join(self.context.goods_to_deliver))


class MessageFormatter(
    Formatter[NewMessageContext],
    key='message',
    name=_('💬 Информация о сообщении ($message)'),
    description=MESSAGE_DESC,
    context_type=NewMessageContext,
):
    def __init__(self, context: NewMessageContext, mode: str, *args, **kwargs) -> None:
        super().__init__(context)
        self.mode = mode

    async def format(self) -> str:
        event = self.context.new_message_event

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
    name=_('👤 Информация о вас ($me)'),
    description=ME_DESC,
    context_type=FormattersContext,
):
    def __init__(
        self,
        context: FormattersContext,
        mode: str = 'username',
        *args,
        **kwargs,
    ) -> None:
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
    name = _('Общее')
    description = _('nodesc')
    include_formatters = {DateTimeFormatter.key, ImageFormatter.key, MeFormatter.key}


class OrderFormattersCategory(FormatterCategory):
    id = 'fph:order'
    name = _('Заказы')
    description = _('nodesc')
    include_formatters = {OrderFormatter.key, GoodsFormatter.key}


class MessageFormattersCategory(FormatterCategory):
    id = 'fph:message'
    name = _('Сообщения')
    description = _('nodesc')
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
