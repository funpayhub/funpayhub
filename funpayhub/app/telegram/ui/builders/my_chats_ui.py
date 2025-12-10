from __future__ import annotations

from typing import Any

from aiogram.types import InlineKeyboardButton

from funpayhub.lib.telegram.ui import Menu, Button, MenuBuilder
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.telegram.callbacks import Dummy
from funpayhub.app.telegram.ui.premade import StripAndNavigationFinalizer
from funpayhub.app.telegram.ui.builders.context import ChatMenuContext, MyChatsMenuContext


class MyChatsUI(MenuBuilder):
    id = MenuIds.my_chats
    context_type = MyChatsMenuContext

    async def build(self, ctx: MyChatsMenuContext, *args: Any, **kwargs: Any) -> Menu:
        keyboard: list[list[Button]] = []
        for i in ctx.chats.chats.values():
            button_text = i.username if not i.is_unread else f'⚡️ {i.username}'
            keyboard.append(
                [
                    Button(
                        button_id=f'my_chat:{i.id}',
                        obj=InlineKeyboardButton(
                            text=button_text,
                            callback_data=Dummy().pack_compact(),
                        ),
                    ),
                ],
            )

        return Menu(
            text='My Chat',
            main_keyboard=[
                [
                    Button(
                        button_id=f'my_chat:{i.id}',
                        obj=InlineKeyboardButton(
                            text=i.username,
                            callback_data=Dummy().pack_compact(),
                        ),
                    ),
                ]
                for i in ctx.chats.chats.values()
            ],
            finalizer=StripAndNavigationFinalizer(),
        )


class ChatUI(MenuBuilder):
    id = MenuIds.chat
    context_type = ChatMenuContext

    async def build(self, ctx: ChatMenuContext, *args: Any, **kwargs: Any) -> Menu: ...
