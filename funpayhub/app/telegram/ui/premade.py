from __future__ import annotations


__all__ = [
    'AddRemoveButtonBaseModification',
    'confirmable_button',
]


from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.ui import MenuModification
from funpayhub.lib.telegram.ui.types import Menu, Button, MenuContext
from funpayhub.lib.base_app.telegram.app.ui.callbacks import Dummy, OpenMenu


def confirmable_button(
    ctx: MenuContext,
    text: str,
    button_id: str,
    unique_id: str,
    translater: Translater,
    callback_data: str = Dummy().pack(),
    style: str | None = None,
) -> list[Button]:
    key = f'{unique_id}:confirm_action'

    if not ctx.data.get(key):
        return Button.callback_button(
            button_id=f'ask_action:{button_id}',
            text=text,
            callback_data=OpenMenu(
                menu_id=ctx.menu_id,
                menu_page=ctx.menu_page,
                view_page=ctx.view_page,
                context_data=ctx.context_data,
                data={**ctx.data, key: True},
                history=ctx.callback_data.history if ctx.callback_data is not None else [],
            ).pack(),
            style=style,
            row=True,
        )

    buttons = [
        Button.callback_button(
            button_id=f'confirm_action:{button_id}',
            text=text,
            callback_data=callback_data,
            style=style,
        ),
        Button.callback_button(
            button_id=f'cancel_action:{button_id}',
            text=translater.translate('🔘 Отмена'),
            callback_data=OpenMenu(
                menu_id=ctx.menu_id,
                menu_page=ctx.menu_page,
                view_page=ctx.view_page,
                context_data=ctx.context_data,
                data={**ctx.data, key: False},
                history=ctx.callback_data.history if ctx.callback_data is not None else [],
            ).pack(),
        ),
    ]

    return buttons


class AddRemoveButtonBaseModification(
    MenuModification,
    modification_id='fph:add_remove_button_base_modification',
):
    """
    Базовая модификация, добавляющая кнопку удаления в подвал клавиатуры.

    Не должна использоваться напрямую.
    """

    async def _modify(
        self,
        ctx: MenuContext,
        menu: Menu,
        translater: Translater,
        delete_callback: str = Dummy().pack(),
    ):
        buttons = confirmable_button(
            ctx=ctx,
            text=translater.translate('🗑️ Удалить'),
            translater=translater,
            button_id='delete',
            unique_id=self.modification_id,
            style='danger',
            callback_data=delete_callback,
        )

        menu.footer_keyboard.add_row(*buttons)
        return menu

    async def modify(self, ctx: MenuContext, menu: Menu):
        raise NotImplementedError()
