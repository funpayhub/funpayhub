from __future__ import annotations


__all__ = [
    'AddRemoveButtonBaseModification',
    'confirmable_button',
]

from funpayhub.lib.translater import translater
from funpayhub.lib.telegram.ui import MenuContext, MenuModification
from funpayhub.lib.telegram.ui.types import Menu, Button, MenuContextOld
from funpayhub.lib.telegram.callback_data import UnknownCallback
from funpayhub.lib.base_app.telegram.app.ui.callbacks import Dummy, OpenMenu

from funpayhub.app.telegram.callbacks import Confirmation


ru = translater.translate


def confirmable_button2(
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
            Button.callback_button(
                button_id=button_id,
                callback_data=callback_data,
                text=text,
                style=style,
            ),
            Button.callback_button(
                button_id=f'cancel_action:{button_id}',
                callback_data=Confirmation(
                    button_id=button_id,
                    open=False,
                    ui_history=ctx.as_ui_history(),
                ).pack(),
                text=ru('🔘 Отмена'),
            ),
        ]
    return [
        Button.callback_button(
            button_id=button_id,
            callback_data=Confirmation(
                button_id=button_id,
                open=True,
                ui_history=ctx.as_ui_history(),
            ).pack(),
            text=text,
            style=style,
        ),
    ]


def confirmable_button(
    ctx: MenuContext,
    text: str,
    confirm_id: str,
    callback_data: str = Dummy().pack(),
    menu_callback_data: UnknownCallback | None = None,
    style: str | None = None,
) -> list[Button]:
    key = f'{confirm_id}:confirm_action'

    callback_data_replace = (
        OpenMenu(
            menu_id=ctx.menu_id,
            menu_page=ctx.menu_page,
            view_page=ctx.view_page,
            context_data=ctx.context_data,
            data={**ctx.data},
            history=ctx.callback_data_history,
        )
        if not menu_callback_data
        else menu_callback_data.model_copy(deep=True)
    )

    exists = ctx.data.get(key) or (
        ctx.callback_data.data.get(key) if ctx.callback_data is not None else False
    )

    if not exists:
        callback_data_replace.data[key] = True
        return Button.callback_button(
            button_id=f'ask_action:{confirm_id}',
            text=text,
            callback_data=callback_data_replace.pack(),
            style=style,
            row=True,
        )

    callback_data_replace.data[key] = False
    return [
        Button.callback_button(
            button_id=f'confirm_action:{confirm_id}',
            text=text,
            callback_data=callback_data,
            style=style,
        ),
        Button.callback_button(
            button_id=f'cancel_action:{confirm_id}',
            text=translater.translate('🔘 Отмена'),
            callback_data=callback_data_replace.pack(),
        ),
    ]


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
        delete_callback: str = Dummy().pack(),
    ):
        buttons = confirmable_button(
            ctx=ctx,
            text=ru('🗑️ Удалить'),
            confirm_id=self.modification_id,
            callback_data=delete_callback,
            style='danger',
        )

        menu.footer_keyboard.add_row(*buttons)
        return menu

    async def modify(self, ctx: MenuContextOld, menu: Menu):
        raise NotImplementedError()
