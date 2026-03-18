from __future__ import annotations


__all__ = [
    'AddRemoveButtonBaseModification',
    'confirmable_button',
]

from funpayhub.lib.translater import translater
from funpayhub.lib.telegram.ui import MenuContext, MenuModification
from funpayhub.lib.telegram.ui.types import Menu, Button, MenuContextOld
from funpayhub.lib.base_app.telegram.app.ui.callbacks import Dummy

from funpayhub.app.telegram.callbacks import Confirmation


ru = translater.translate


def confirmable_button(
    ctx: MenuContext,
    button_id: str,
    text: str,
    callback_data: str = Dummy().pack(),
    style: str | None = None,
) -> list[Button]:
    key = f'open_confirmation:{button_id}'
    has_key = ctx.data.get(key)

    if has_key:
        return [
            Button.callback_button(button_id, text, callback_data, style),
            Button.callback_button(
                f'cancel_action:{button_id}',
                ru('🔘 Отмена'),
                Confirmation(
                    button_id=button_id, open=False, ui_history=ctx.as_ui_history()
                ).pack(),
            ),
        ]
    return Button.callback_button(
        button_id,
        text,
        Confirmation(button_id=button_id, open=True, ui_history=ctx.as_ui_history()).pack(),
        style,
        row=True,
    )


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
        button_id: str,
        delete_callback: str = Dummy().pack(),
    ) -> Menu:
        buttons = confirmable_button(
            ctx=ctx,
            button_id=button_id,
            text=ru('🗑️ Удалить'),
            callback_data=delete_callback,
            style='danger',
        )

        menu.footer_keyboard.add_row(*buttons)
        return menu

    async def modify(self, ctx: MenuContextOld, menu: Menu):
        raise NotImplementedError()
