from __future__ import annotations

import html
from typing import TYPE_CHECKING

from pydantic import Field
from hubplatform.i18n import I18nString
from funpaybotengine.types import Message
from hubplatform.telegram.ui import (
    MenuSpec,
    UIRegistry,
    MenuContext,
    MenuBuildContext,
    MenuBuildingSpec,
)
from funpaybotengine.types.enums import BadgeType

from .menu_ids import NewFunPayMessageUIMenuIDs


if TYPE_CHECKING:
    from funpayhub.app.components import FunPayComponent


registry = UIRegistry()


class NewFunPayMessageMenuContext(MenuContext):
    funpay_chat_name: str
    funpay_chat_id: int
    messages: list[Message] = Field(default_factory=list)


_prefixes_by_badge_type = {
    BadgeType.AUTO_DELIVERY: '📦',
    BadgeType.SUPPORT: '🟢',
    BadgeType.NOTIFICATIONS: '🔵',
}


async def gen_user_info(msg: Message, funpay_component: FunPayComponent) -> str:
    username = msg.sender_username
    if msg.badge:
        return f'{_prefixes_by_badge_type.get(msg.badge.type, "")}{username} ({msg.badge.text})'

    prefix = '👤'
    if msg.sender_id == funpay_component.bot.userid:
        automatic = await funpay_component.is_automatic_message(msg.id)
        if automatic:
            prefix = '🤖'
        else:
            prefix = '😎'
    return f'{prefix}{username}'


@registry.add_menu_builder(
    menu_id=NewFunPayMessageUIMenuIDs.new_message,
    context_type=NewFunPayMessageMenuContext,
)
async def build_new_funpay_message_menu(
    ctx: MenuBuildContext[NewFunPayMessageMenuContext],
    funpay_component: FunPayComponent,
) -> MenuBuildingSpec:
    menu = MenuSpec()
    if not ctx.context.messages:
        raise ValueError('No messages in context.')

    texts: list[str] = []
    for msg in ctx.context.messages:
        if msg.sender_id == 0:
            if not msg.text:
                continue

            texts.append(f'<blockquote><b>{html.escape(msg.text)}</b></blockquote>')
            continue

        user_info = await gen_user_info(msg, funpay_component)
        user_info = f'<a href="https://funpay.com/users/{msg.sender_id}/">{user_info}</a>'
        if msg.text:
            text = html.escape(msg.text)
            if msg.sender_id == 0:
                text = f'<b>{text}</b>'
        elif msg.image_url:
            text = f'\n<img src="{msg.image_url}"/>'
        else:
            text = ''
        texts.append(f'{user_info}: {text}')

    menu.body_text = '\n\n'.join(texts)
    menu.footer_text = I18nString(
        f'<i>Чат: <a href="https://funpay.com/chat/?node={ctx.context.funpay_chat_id}">'
        f'{ctx.context.funpay_chat_name} ({ctx.context.funpay_chat_id})'
        f'</a></i>',
    )
    return MenuBuildingSpec(menu=menu)
