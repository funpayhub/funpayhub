from __future__ import annotations


__all__ = [
    'AddRemoveButtonBaseModification',
]


from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.ui import MenuModification
from funpayhub.lib.telegram.ui.types import Menu, Button, MenuContext
from funpayhub.lib.base_app.telegram.app.ui.callbacks import Dummy, OpenMenu


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
        key = f'{self.modification_id}:confirm_delete'

        if not ctx.data.get(key):
            menu.footer_keyboard.add_callback_button(
                button_id='delete',
                text=translater.translate('$delete'),
                callback_data=OpenMenu(
                    menu_id=ctx.menu_id,
                    menu_page=ctx.menu_page,
                    view_page=ctx.view_page,
                    context_data=ctx.context_data,
                    data={**ctx.data, key: True},
                    history=ctx.callback_data.history if ctx.callback_data is not None else [],
                ).pack(),
                style='danger',
            )
        else:
            menu.footer_keyboard.add_row(
                Button.callback_button(
                    button_id='confirm_delete',
                    text=translater.translate('$delete'),
                    callback_data=delete_callback,
                    style='danger',
                ),
                Button.callback_button(
                    button_id='cancel_delete',
                    text=translater.translate('$cancel'),
                    callback_data=OpenMenu(
                        menu_id=ctx.menu_id,
                        menu_page=ctx.menu_page,
                        view_page=ctx.view_page,
                        context_data=ctx.context_data,
                        data={**ctx.data, key: False},
                        history=ctx.callback_data.history if ctx.callback_data is not None else [],
                    ).pack(),
                ),
            )
        return menu

    async def modify(self, ctx: MenuContext, menu: Menu):
        raise NotImplementedError()
