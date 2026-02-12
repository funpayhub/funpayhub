from __future__ import annotations

import html
from typing import TYPE_CHECKING

from funpaybotengine import Bot as FPBot
from funpaybotengine.types.enums import BadgeType

from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.ui.types import Menu, Button, MenuBuilder, KeyboardBuilder
from funpayhub.lib.base_app.telegram.app.ui.callbacks import ClearState
from funpayhub.lib.base_app.telegram.app.ui.ui_finalizers import StripAndNavigationFinalizer

import funpayhub.app.telegram.callbacks as cbs
from funpayhub.app.properties import FunPayHubProperties

from ..ids import MenuIds
from .context import NewMessageMenuContext, SendMessageMenuContext


if TYPE_CHECKING:
    from funpayhub.app.funpay.main import FunPay


_prefixes_by_badge_type = {
    BadgeType.AUTO_DELIVERY: '📦',
    BadgeType.SUPPORT: '🟢',
    BadgeType.NOTIFICATIONS: '🔵',
}


class NewMessageNotificationMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.new_funpay_message,
    context_type=NewMessageMenuContext,
):
    async def build(
        self,
        ctx: NewMessageMenuContext,
        translater: Translater,
        fp_bot: FPBot,
        fp: FunPay,
    ) -> Menu:
        # Не хэшируем коллбэки данного меню, чтобы не забивать память.
        # Вместо этого делаем коротки коллбэки, чтобы они могли работать между перезапусками.
        keyboard = KeyboardBuilder()
        keyboard.add_row(
            Button.callback_button(
                button_id='reply',
                text=translater.translate('🗨️ Ответить'),
                callback_data=cbs.SendMessage(
                    to=ctx.funpay_chat_id,
                    name=ctx.funpay_chat_name,
                ).pack_compact(),
            ),
            Button.callback_button(
                button_id='mute',
                text=translater.translate('🔕 Не уведомлять'),
                callback_data=cbs.MuteChat(chat_id=ctx.funpay_chat_id).pack_compact(),
            ),
            Button.url_button(
                button_id='open_chat',
                text=translater.translate('🌐 Чат'),
                url=f'https://funpay.com/chat/?node={ctx.funpay_chat_id}',
            ),
        )

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
                    if (
                        await fp_bot.storage.is_message_sent_by_bot(msg.id)
                    ) and not fp.is_manual_message(msg.id):
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

        header_text = (
            f'✉️ <b>Новые сообщения в чате <code>{ctx.funpay_chat_name}</code> '
            f'(ID: <code>{ctx.funpay_chat_id}</code>).</b>'
        )

        return Menu(
            header_text=header_text,
            main_text=text,
            header_keyboard=keyboard,
            finalizer=StripAndNavigationFinalizer(),
        )


class SendMessageMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.send_funpay_message,
    context_type=SendMessageMenuContext,
):
    async def build(
        self,
        ctx: SendMessageMenuContext,
        properties: FunPayHubProperties,
        translater: Translater,
    ) -> Menu:
        keyboard = KeyboardBuilder()
        for index, i in enumerate(properties.message_templates.value):
            keyboard.add_callback_button(
                button_id=f'send_template:{index}',
                text=i[:30] + ('...' if len(i) > 30 else ''),
                callback_data=cbs.SendTemplate(to=ctx.funpay_chat_id, index=index).pack_compact(),
            )

        return Menu(
            main_text=translater.translate(
                '<b>Отправьте сообщение или изображение пользователю <a href="https://funpay.com/chat/?node={chat_id}">{chat_name}</a>.</b>',
            ).format(
                chat_id=ctx.funpay_chat_id,
                chat_name=ctx.funpay_chat_name,
            ),
            footer_keyboard=KeyboardBuilder(
                keyboard=[
                    Button.callback_button(
                        button_id='cancel',
                        text=translater.translate('🔘 Отмена'),
                        callback_data=ClearState(delete_message=True).pack(),
                        row=True,
                    ),
                ],
            ),
            main_keyboard=keyboard,
            finalizer=StripAndNavigationFinalizer(back_button=False),
        )
