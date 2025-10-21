from __future__ import annotations

import html

from aiogram.types import InlineKeyboardButton

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.ui.types import Menu, Button
from .context import NewMessageMenuContext


async def message_menu_builder(
    ctx: NewMessageMenuContext,
    properties: FunPayHubProperties,
    translater: Translater,
) -> Menu:
    language = properties.general.language.real_value

    keyboard = [
        [
            Button(
                button_id='reply',
                obj=InlineKeyboardButton(
                    text=translater.translate('$reply', language),
                    callback_data='reply',
                ),
            ),
            Button(
                button_id='block',
                obj=InlineKeyboardButton(
                    text=translater.translate('$block', language),
                    callback_data=cbs.Dummy().pack(),
                ),
            ),
            Button(
                button_id='open_chat',
                obj=InlineKeyboardButton(
                    text=translater.translate('$open_chat', language),
                    url=f'https://funpay.com/chat/?node={ctx.funpay_chat_id}'
                )
            )
        ],
    ]

    if ctx.messages:
        texts = []
        for msg in ctx.messages:
            username = msg.sender_username
            if msg.badge:
                username += f' ({msg.badge.text})'
            if msg.sender_id == 0:
                username = f'🔵{username}'
            else:
                username = f'👤{username}'

            texts.append(
                f'<a href="https://funpay.com/users/{msg.sender_id}/">{username}</a>'
                f'<blockquote>'
                f'{html.escape(msg.text or msg.image_url)}'
                f'</blockquote>'
            )
        text = '\n\n'.join(texts)
    else:
        text = (f'<pre><code class="language-❔ Unknown sender">'
                f'❌ No messages in menu context :('
                f'</code></pre>')

    text = f'✉️ <b>Новые сообщения в чате <code>{ctx.funpay_chat_name}</code>.</b>\n\n' + text

    return Menu(text=text, header_keyboard=keyboard)
