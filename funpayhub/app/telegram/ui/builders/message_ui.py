from __future__ import annotations

import html

from aiogram.types import InlineKeyboardButton
from funpaybotengine import Bot as FPBot
from funpaybotengine.types.enums import BadgeType

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.ui.types import Menu, Button, MenuBuilder

from ..ids import MenuIds
from .context import NewMessageMenuContext, SendMessageMenuContext
from ..premade import default_finalizer_factory


_prefixes_by_badge_type = {
    BadgeType.AUTO_DELIVERY: '📦',
    BadgeType.SUPPORT: '🟢',
    BadgeType.NOTIFICATIONS: '🔵',
}


class NewMessageNotificationMenuBuilder(MenuBuilder):
    id = MenuIds.new_funpay_message
    context_type = NewMessageMenuContext

    async def build(
        self,
        ctx: NewMessageMenuContext,
        translater: Translater,
        fp_bot: FPBot,
    ) -> Menu:
        # Не хэшируем коллбэки данного меню, чтобы не забивать память.
        # Вместо этого делаем коротки коллбэки, чтобы они могли работать между перезапусками.
        keyboard = [
            [
                Button(
                    button_id='reply',
                    obj=InlineKeyboardButton(
                        text=translater.translate('$reply'),
                        callback_data=cbs.SendMessage(to=ctx.funpay_chat_id).pack(hash=False),
                    ),
                ),
                Button(
                    button_id='mute',
                    obj=InlineKeyboardButton(
                        text=translater.translate('$mute'),
                        callback_data=cbs.MuteChat(chat_id=ctx.funpay_chat_id).pack(hash=False),
                    ),
                ),
                Button(
                    button_id='open_chat',
                    obj=InlineKeyboardButton(
                        text=translater.translate('$open_chat'),
                        url=f'https://funpay.com/chat/?node={ctx.funpay_chat_id}',
                    ),
                ),
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
                    f'<blockquote>{msg_text}</blockquote>',
                )
            text = '\n\n'.join(texts)
        else:
            text = (
                '<pre><code class="language-❔ Unknown sender">'
                '❌ No messages in menu context :('
                '</code></pre>'
            )

        text = (
            f'✉️ <b>Новые сообщения в чате <code>{ctx.funpay_chat_name}</code> '
            f'(ID: <code>{ctx.funpay_chat_id}</code>).</b>\n\n'
        ) + text

        return Menu(
            text=text,
            header_keyboard=keyboard,
            finalizer=default_finalizer_factory(),
        )


class SendMessageMenuBuilder(MenuBuilder):
    id = MenuIds.send_funpay_message
    context_type = SendMessageMenuContext

    async def build(
        self,
        ctx: SendMessageMenuContext,
        properties: FunPayHubProperties,
        translater: Translater,
    ) -> Menu:
        kb = []
        for index, i in enumerate(properties.message_templates.value):
            kb.append(
                [
                    Button(
                        button_id=f'send_template:{index}',
                        obj=InlineKeyboardButton(
                            text=i[:30] + ('...' if len(i) > 30 else ''),
                            callback_data=cbs.SendTemplate(
                                to=ctx.funpay_chat_id, index=index
                            ).pack(hash=False),
                        ),
                    )
                ]
            )

        return Menu(
            text='$enter_message_text',
            footer_keyboard=[
                [
                    Button(
                        button_id='cancel',
                        obj=InlineKeyboardButton(
                            text=translater.translate('$clear_state'),
                            callback_data=cbs.Clear(delete_message=True).pack(),
                        ),
                    ),
                ]
            ],
            main_keyboard=kb,
            finalizer=default_finalizer_factory(back_button=False),
        )
