from __future__ import annotations

import html
from typing import TYPE_CHECKING

from aiogram.types import InlineKeyboardButton

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.ui.types import Menu, Button, MenuContext


if TYPE_CHECKING:
    from funpayhub.lib.telegram.ui import UIRegistry


async def message_menu_builder(
    ctx: MenuContext,
    properties: FunPayHubProperties,
    translater: Translater,
) -> Menu:
    message_text = ctx.data['message_text']
    sender_username = ctx.data['sender_username']
    sender_id = ctx.data['sender_id']

    keyboard = [
        [
            Button(
                button_id='1',
                obj=InlineKeyboardButton(
                    text='Ответить',
                    callback_data=cbs.Dummy().pack(),
                ),
            ),
            Button(
                button_id='2',
                obj=InlineKeyboardButton(
                    text='Послать нахуй',
                    callback_data=cbs.Dummy().pack(),
                ),
            ),
        ],
    ]

    return Menu(
        text=f'<pre><code class="language-{sender_username}">{html.escape(message_text)}</code></pre>',
        main_keyboard=keyboard,
    )
