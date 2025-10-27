from __future__ import annotations


__all__ = [
    'build_menu_navigation_buttons',
    'build_view_navigation_buttons',
    'default_finalizer_factory',
]

import math

from aiogram.types import InlineKeyboardButton

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.ui.types import Menu, Button, Keyboard, MenuContext


async def build_menu_navigation_buttons(
    ctx: MenuContext,
    translater: Translater,
    total_pages: int,
    back_button: bool = True,
) -> Keyboard:
    kb: Keyboard = []
    callback_data = ctx.callback_data
    if callback_data is None:
        return kb

    if callback_data.history and back_button:
        kb = [
            [
                Button(
                    button_id='back',
                    obj=InlineKeyboardButton(
                        text=translater.translate('$back'),
                        callback_data=callback_data.pack_history(),
                    ),
                ),
            ],
        ]

    if total_pages < 2:
        return kb

    page_amount_btn = Button(
        button_id='menu_page_counter',
        obj=InlineKeyboardButton(
            text=f'{ctx.menu_page + (1 if total_pages else 0)} / {total_pages}',
            callback_data=cbs.ChangeMenuPageManually(
                total_pages=total_pages,
                history=callback_data.as_history(),
            ).pack()
            if total_pages > 1
            else cbs.Dummy().pack(),
        ),
    )

    to_first_btn = Button(
        button_id='to_first_menu_page',
        obj=InlineKeyboardButton(
            text='⏪' if ctx.menu_page > 0 else ' ',
            callback_data=cbs.ChangePageTo(
                menu_page=0,
                history=callback_data.as_history(),
            ).pack()
            if ctx.menu_page > 0
            else cbs.Dummy().pack(),
        ),
    )

    to_last_btn = Button(
        button_id='to_last_menu_page',
        obj=InlineKeyboardButton(
            text='⏩' if ctx.menu_page < total_pages - 1 else ' ',
            callback_data=cbs.ChangePageTo(
                menu_page=total_pages - 1,
                history=callback_data.as_history(),
            ).pack()
            if ctx.menu_page < total_pages - 1
            else cbs.Dummy().pack(),
        ),
    )

    to_previous_btn = Button(
        button_id='to_previous_menu_page',
        obj=InlineKeyboardButton(
            text='◀️' if ctx.menu_page > 0 else ' ',
            callback_data=cbs.ChangePageTo(
                menu_page=ctx.menu_page - 1,
                history=callback_data.as_history(),
            ).pack()
            if ctx.menu_page > 0
            else cbs.Dummy().pack(),
        ),
    )

    to_next_btn = Button(
        button_id='to_next_menu_page',
        obj=InlineKeyboardButton(
            text='▶️' if ctx.menu_page < total_pages - 1 else ' ',
            callback_data=cbs.ChangePageTo(
                menu_page=ctx.menu_page + 1,
                history=callback_data.as_history(),
            ).pack()
            if ctx.menu_page < total_pages - 1
            else cbs.Dummy().pack(),
        ),
    )

    kb.insert(0, [to_first_btn, to_previous_btn, page_amount_btn, to_next_btn, to_last_btn])
    return kb


async def build_view_navigation_buttons(ctx: MenuContext, total_pages: int) -> Keyboard:
    kb: Keyboard = []
    callback_data = ctx.callback_data
    if callback_data is None or total_pages < 2:
        return kb

    page_amount_btn = Button(
        button_id='menu_page_counter',
        obj=InlineKeyboardButton(
            text=f'{ctx.view_page + (1 if total_pages else 0)} / {total_pages}',
            callback_data=cbs.ChangeViewPageManually(
                total_pages=total_pages,
                history=callback_data.as_history() if callback_data.history else None,
            ).pack()
            if total_pages > 1
            else cbs.Dummy().pack(),
        ),
    )

    to_first_btn = Button(
        button_id='to_first_menu_page',
        obj=InlineKeyboardButton(
            text='⏪' if ctx.view_page > 0 else ' ',
            callback_data=cbs.ChangePageTo(
                view_page=0,
                history=callback_data.as_history() if callback_data.history else None,
            ).pack()
            if ctx.view_page > 0
            else cbs.Dummy().pack(),
        ),
    )

    to_last_btn = Button(
        button_id='to_last_menu_page',
        obj=InlineKeyboardButton(
            text='⏩' if ctx.view_page < total_pages - 1 else ' ',
            callback_data=cbs.ChangePageTo(
                view_page=total_pages - 1,
                history=callback_data.as_history() if callback_data.history else None,
            ).pack()
            if ctx.view_page < total_pages - 1
            else cbs.Dummy().pack(),
        ),
    )

    to_previous_btn = Button(
        button_id='to_previous_menu_page',
        obj=InlineKeyboardButton(
            text='◀️' if ctx.view_page > 0 else ' ',
            callback_data=cbs.ChangePageTo(
                view_page=ctx.view_page - 1,
                history=callback_data.as_history() if callback_data.history else None,
            ).pack()
            if ctx.view_page > 0
            else cbs.Dummy().pack(),
        ),
    )

    to_next_btn = Button(
        button_id='to_next_menu_page',
        obj=InlineKeyboardButton(
            text='▶️' if ctx.view_page < total_pages - 1 else ' ',
            callback_data=cbs.ChangePageTo(
                view_page=ctx.view_page + 1,
                history=callback_data.as_history() if callback_data.history else None,
            ).pack()
            if ctx.view_page < total_pages - 1
            else cbs.Dummy().pack(),
        ),
    )

    kb.insert(0, [to_first_btn, to_previous_btn, page_amount_btn, to_next_btn, to_last_btn])
    return kb


def default_finalizer_factory(back_button: bool = True, max_lines_on_page: int | None = None):
    async def _default_finalizer(
        ctx: MenuContext,
        menu: Menu,
        properties: FunPayHubProperties,
        translater: Translater,
    ) -> Menu:
        if not menu.footer_keyboard:
            menu.footer_keyboard = []
        max_lines = max_lines_on_page or properties.telegram.appearance.menu_entries_amount.value

        total_pages = (
            math.ceil(
                len(menu.main_keyboard) / max_lines,
            )
            if menu.main_keyboard
            else 0
        )

        navigation_buttons = await build_menu_navigation_buttons(
            ctx=ctx,
            translater=translater,
            total_pages=total_pages,
            back_button=back_button,
        )
        menu.footer_keyboard.extend(navigation_buttons)

        if menu.main_keyboard:
            first_index = ctx.menu_page * max_lines
            last_index = first_index + max_lines
            menu.main_keyboard = menu.main_keyboard[first_index:last_index]

        return menu

    return _default_finalizer
