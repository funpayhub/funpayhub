from __future__ import annotations

import time
from typing import TYPE_CHECKING, Literal
from datetime import datetime

from hubplatform.telegram.ui import (
    Button,
    MenuSpec,
    UIRegistry,
    MenuContext,
    MenuBuildContext,
    MenuBuildingSpec,
    KeyboardBlockSpec,
)
from hubplatform.telegram.callback_data.hash import HashService
from hubplatform.app.components.telegram.ui.widgets import cancel_button, confirmable_button
from hubplatform.app.components.telegram.ui.callbacks import OpenMenu
from hubplatform.app.components.telegram.ui.finalizers import StripAndNavigationFinalizer
from hubplatform.app.components.telegram.properties.callbacks import ManualValueInput

from ..menu_ids import MenuIDs as ExtensionMenuIDs
from .callbacks import StartChatInput, RemoveChatFromCache, SetChatTimestampToNow


if TYPE_CHECKING:
    from dothub.app.components.funpay_component import FunPayProperties
    from dothub.app.components.funpay_component.first_response_cache import FirstResponseCache


TIME_FORMAT = '%d.%m %H.%M.%S'
TIME_FORMAT_HINT = 'ДД.ММ ЧЧ.ММ.СС'


def format_ts(ts: int) -> str:
    return datetime.fromtimestamp(ts).strftime(TIME_FORMAT)


def parse_ts(text: str) -> int:
    """Parses ``TIME_FORMAT`` (current year is assumed) into a unix timestamp."""
    year = datetime.now().year
    return int(datetime.strptime(f'{year}.{text.strip()}', f'%Y.{TIME_FORMAT}').timestamp())


def format_duration(seconds: int) -> str:
    """``90061`` -> ``'1 д 1 ч 1 мин 1 сек'``."""
    parts = []
    for unit, size in (('д', 86400), ('ч', 3600), ('мин', 60), ('сек', 1)):
        amount, seconds = divmod(seconds, size)
        if amount:
            parts.append(f'{amount} {unit}')
    return ' '.join(parts) or '0 сек'


class ChatMenuContext(MenuContext):
    chat_id: int


class ChatInputMenuContext(MenuContext):
    action: Literal['add', 'set_time']
    return_session_id: str
    chat_id: int | None = None


registry = UIRegistry()


@registry.add_menu_builder(menu_id=ExtensionMenuIDs.first_response_cache.chats_list)
async def chats_list_menu(
    ctx: MenuBuildContext[MenuContext],
    first_response_cache: FirstResponseCache,
    funpay_props: FunPayProperties,
    hash_service: HashService,
) -> MenuBuildingSpec:
    menu = MenuSpec()
    menu.header_text = '<h2>✉️ Кэш приветствий</h2>'

    chats = await first_response_cache.get_all()
    reset_after = funpay_props.first_response.timeout.value
    now = time.time()

    edit_reset_after_button = Button(
        button_id='edit_reset_after',
        text='✏️ Изменить',
        callback_data=ManualValueInput(node_path=list(funpay_props.first_response.timeout.path)),
    )
    reset_text = (
        f'<b>⏱ Время сброса: {format_duration(reset_after)}</b> '
        f'{edit_reset_after_button.to_html(hash_service)}'
        '<p><i>Через это время после приветствия чат снова считается новым.</i></p>'
        '<hr/>'
    )
    if chats:
        active = sum(1 for ts in chats.values() if ts + reset_after > now)
        menu.body_text = (
            reset_text
            + f'<p>Чатов в кэше: <b>{len(chats)}</b>, из них ждут сброса: <b>{active}</b>.</p>'
            '<p>⏳ — приветствие сейчас не будет отправлено.<br/>'
            '🟢 — чат снова считается новым.</p>'
            '<i>Выберите чат, чтобы изменить или удалить его.</i>'
        )
    else:
        menu.body_text = reset_text + '<p>Кэш пуст: приветствие ещё никому не отправлялось.</p>'

    for chat_id, ts in chats.items():
        status = '⏳' if ts + reset_after > now else '🟢'
        menu.main_keyboard.append(
            KeyboardBlockSpec.callback_button(
                block_id=f'app:funpay_component:first_response_cache:chat:{chat_id}',
                text=f'{status} {chat_id} · {format_ts(ts)}',
                callback_data=OpenMenu(
                    menu_id=ExtensionMenuIDs.first_response_cache.chat,
                    context=ChatMenuContext(chat_id=chat_id).dump(),
                ),
            ),
        )

    menu.footer_keyboard.append(
        KeyboardBlockSpec.callback_button(
            block_id='app:funpay_component:first_response_cache:add_chat',
            text='➕ Добавить чат',
            callback_data=StartChatInput(action='add'),
            style='success',
        ),
    )

    return MenuBuildingSpec(menu=menu, finalizer=StripAndNavigationFinalizer())


@registry.add_menu_builder(
    menu_id=ExtensionMenuIDs.first_response_cache.chat,
    context_type=ChatMenuContext,
)
class ChatMenuBuilder:
    async def __call__(
        self,
        ctx: MenuBuildContext[ChatMenuContext],
        first_response_cache: FirstResponseCache,
        funpay_props: FunPayProperties,
    ) -> MenuBuildingSpec:
        chat_id = ctx.context.chat_id
        menu = MenuSpec()
        menu.header_text = f'<h2>💬 Чат <code>{chat_id}</code></h2>'

        ts = await first_response_cache.get(chat_id)
        if ts == -1:
            menu.body_text = (
                '<p>Чата нет в кэше: при следующем сообщении будет отправлено приветствие.</p>'
            )
        else:
            reset_at = ts + funpay_props.first_response.timeout.value
            status = (
                f'⏳ Сбросится {format_ts(reset_at)}'
                if reset_at > time.time()
                else '🟢 Чат снова считается новым'
            )
            menu.body_text = (
                '<table bordered striped compact>'
                f'<tr><td>ID чата</td><td><code>{chat_id}</code></td></tr>'
                f'<tr><td>Последнее приветствие</td><td>{format_ts(ts)}</td></tr>'
                f'<tr><td>Статус</td><td>{status}</td></tr>'
                '</table>'
            )

        menu.main_keyboard.append(
            KeyboardBlockSpec.prerendered_block(
                block_id='app:funpay_component:first_response_cache:set',
                block=[
                    Button(
                        button_id='set_now',
                        text='🕒 Отметить сейчас',
                        callback_data=SetChatTimestampToNow(chat_id=chat_id),
                    ),
                    Button(
                        button_id='set_time',
                        text='✏️ Указать время',
                        callback_data=StartChatInput(action='set_time', chat_id=chat_id),
                    ),
                ],
            ),
        )
        menu.main_keyboard.append(
            KeyboardBlockSpec.url_button(
                block_id='app:funpay_component:first_response_cache:open_chat',
                text='🌐 Открыть чат',
                url=f'https://funpay.com/chat/?node={chat_id}',
            ),
        )

        if ts != -1:
            menu.footer_keyboard.append(
                KeyboardBlockSpec.prerendered_block(
                    block_id='app:funpay_component:first_response_cache:remove',
                    block=confirmable_button(
                        id='remove_chat',
                        ctx=ctx.context,
                        text='🗑 Удалить из кэша',
                        callback_data=RemoveChatFromCache(chat_id=chat_id),
                        style='danger',
                    ),
                ),
            )

        return MenuBuildingSpec(menu=menu, finalizer=StripAndNavigationFinalizer())


@registry.add_menu_builder(
    menu_id=ExtensionMenuIDs.first_response_cache.chat_input,
    context_type=ChatInputMenuContext,
)
async def chat_input_menu(ctx: MenuBuildContext[ChatInputMenuContext]) -> MenuBuildingSpec:
    menu = MenuSpec()

    if ctx.context.action == 'add':
        menu.header_text = '<h2>➕ Добавление чата</h2>'
        menu.body_text = (
            '<p>Отправьте ID чата.</p>'
            '<i>Чат будет отмечен текущим временем, '
            'и приветствие в нём не отправится до сброса.</i>'
        )
    else:
        menu.header_text = f'<h2>✏️ Время для чата <code>{ctx.context.chat_id}</code></h2>'
        menu.body_text = (
            f'<p>Отправьте время в формате <code>{TIME_FORMAT_HINT}</code>.</p>'
            f'<p>Например: <code>{format_ts(int(time.time()))}</code>.</p>'
            '<i>Год берётся текущий.</i>'
        )

    menu.footer_keyboard.append(
        KeyboardBlockSpec.prerendered_block(
            block_id='cancel',
            block=cancel_button(open_session_id=ctx.context.return_session_id),
        ),
    )
    return MenuBuildingSpec(menu=menu, finalizer=StripAndNavigationFinalizer())
