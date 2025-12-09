from __future__ import annotations

from typing import Any

from aiogram.types import InlineKeyboardButton

from funpayhub.lib.telegram.ui import Menu, Button, MenuBuilder
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.telegram.callbacks import Dummy
from funpayhub.app.telegram.ui.premade import StripAndNavigationFinalizer
from funpayhub.app.telegram.ui.builders.context import MyChatsMenuContext


class MyChatsUI(MenuBuilder):
    id = MenuIds.my_chats
    context_type = MyChatsMenuContext

    async def build(self, ctx: MyChatsMenuContext, *args: Any, **kwargs: Any) -> Menu:
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
