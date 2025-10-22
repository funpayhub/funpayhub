from __future__ import annotations

import html

from aiogram.types import InlineKeyboardButton

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.ui.types import Menu, Button
from funpaybotengine.types.enums import BadgeType, MessageType
from funpaybotengine import Bot as FPBot
from .context import NewMessageMenuContext


_prefixes_by_badge_type = {
    BadgeType.AUTO_DELIVERY: '📦',
    BadgeType.SUPPORT: '🟢',
    BadgeType.NOTIFICATIONS: '🔵',
}


async def message_menu_builder(
    ctx: NewMessageMenuContext,
    properties: FunPayHubProperties,
    translater: Translater,
    fp_bot: FPBot
) -> Menu:
    language = properties.general.language.real_value

    # Не хэшируем коллбэки данного меню, чтобы не забивать память.
    # Вместо этого делаем коротки коллбэки, чтобы они могли работать между перезапусками.
    keyboard = [
        [
            Button(
                button_id='reply',
                obj=InlineKeyboardButton(
                    text=translater.translate('$reply', language),
                    callback_data=cbs.SendMessage(to=ctx.funpay_chat_id).pack(hash=False),
                ),
            ),
            Button(
                button_id='mute',
                obj=InlineKeyboardButton(
                    text=translater.translate('$mute', language),
                    callback_data=cbs.MuteChat(chat_id=ctx.funpay_chat_id).pack(hash=False),
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
            msg_text = html.escape(msg.text or msg.image_url)

            prefix = '👤'
            if msg.badge:
                username += f' ({msg.badge.text})'
                prefix = _prefixes_by_badge_type.get(msg.badge.type, '')
            elif msg.sender_id == fp_bot.userid:
                if await fp_bot.storage.is_message_sent_by_bot(msg.id):
                    prefix = '🤖'
                else:
                    prefix = '😎'

            if msg.sender_id == 0:
                msg_text = f'<b>{msg_text}</b>'

            username = ' '.join([prefix, username])

            texts.append(
                f'<a href="https://funpay.com/users/{msg.sender_id}/">{username}</a> - '
                f'<i>{msg.send_date_text}</i>\n'
                f'<blockquote>{msg_text}</blockquote>'
            )
        text = '\n\n'.join(texts)
    else:
        text = (f'<pre><code class="language-❔ Unknown sender">'
                f'❌ No messages in menu context :('
                f'</code></pre>')

    text = (f'✉️ <b>Новые сообщения в чате <code>{ctx.funpay_chat_name}</code> '
            f'(ID: <code>{ctx.funpay_chat_id}</code>).</b>\n\n') + text

    return Menu(text=text, header_keyboard=keyboard)
