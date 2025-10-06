from __future__ import annotations


__all__ = [
    'build_menu_navigation_buttons',
    'build_view_navigation_buttons',
    'default_finalizer_factory'
]

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.lib.telegram.ui import Button, Keyboard, UIContext, UIRegistry, Menu
import math


async def build_menu_navigation_buttons(ui: UIRegistry, ctx: UIContext, total_pages: int, back_button: bool = True) -> Keyboard:
    kb = []
    if ctx.callback.history and back_button:
        kb = [[
            Button(
                button_id='back',
                text=ui.translater.translate('$back', ctx.language),
                callback_data=ctx.callback.pack_history(),
            )
        ]]

    if total_pages < 2:
        return kb

    page_amount_btn = Button(
        button_id='menu_page_counter',
        text=f'{ctx.menu_page + (1 if total_pages else 0)} / {total_pages}',
        callback_data=cbs.ChangeMenuPageManually(
            total_pages=total_pages,
            history=[ctx.callback.pack()]
        ).pack() if total_pages > 1 else cbs.Dummy().pack()
    )

    to_first_btn = Button(
        button_id='to_first_menu_page',
        text='⏪' if ctx.menu_page > 0 else '❌',
        callback_data=cbs.ChangePageTo(
            menu_page=0,
            history=[ctx.callback.pack()]
        ).pack() if ctx.menu_page > 0 else cbs.Dummy().pack(),
    )

    to_last_btn = Button(
        button_id='to_last_menu_page',
        text='⏩' if ctx.menu_page < total_pages - 1 else '❌',
        callback_data=cbs.ChangePageTo(
            menu_page=total_pages - 1,
            history=[ctx.callback.pack()]
        ).pack() if ctx.menu_page < total_pages - 1 else cbs.Dummy().pack(),
    )

    to_previous_btn = Button(
        button_id='to_previous_menu_page',
        text='◀️' if ctx.menu_page > 0 else '❌',
        callback_data=cbs.ChangePageTo(
            menu_page=ctx.menu_page - 1,
            history=[ctx.callback.pack()]
        ).pack() if ctx.menu_page > 0 else cbs.Dummy().pack(),
    )

    to_next_btn = Button(
        button_id='to_next_menu_page',
        text='▶️' if ctx.menu_page < total_pages - 1 else '❌',
        callback_data=cbs.ChangePageTo(
            menu_page=ctx.menu_page + 1,
            history=[ctx.callback.pack()]
        ).pack() if ctx.menu_page < total_pages - 1 else cbs.Dummy().pack(),
    )

    kb.insert(0, [to_first_btn, to_previous_btn, page_amount_btn, to_next_btn, to_last_btn])
    return kb


async def build_view_navigation_buttons(ctx: UIContext, total_pages: int) -> Keyboard:
    kb = []

    if total_pages < 2:
        return kb

    page_amount_btn = Button(
        button_id='menu_page_counter',
        text=f'{ctx.view_page + (1 if total_pages else 0)} / {total_pages}',
        callback_data=cbs.ChangeViewPageManually(
            total_pages=total_pages,
            history=[ctx.callback.pack()]
        ).pack() if total_pages > 1 else cbs.Dummy().pack()
    )

    to_first_btn = Button(
        button_id='to_first_menu_page',
        text='⏪' if ctx.view_page > 0 else '❌',
        callback_data=cbs.ChangePageTo(
            view_page=0,
            history=[ctx.callback.pack()]
        ).pack() if ctx.view_page > 0 else cbs.Dummy().pack(),
    )

    to_last_btn = Button(
        button_id='to_last_menu_page',
        text='⏩' if ctx.view_page < total_pages - 1 else '❌',
        callback_data=cbs.ChangePageTo(
            view_page=total_pages - 1,
            history=[ctx.callback.pack()]
        ).pack() if ctx.view_page < total_pages - 1 else cbs.Dummy().pack(),
    )

    to_previous_btn = Button(
        button_id='to_previous_menu_page',
        text='◀️' if ctx.view_page > 0 else '❌',
        callback_data=cbs.ChangePageTo(
            view_page=ctx.view_page - 1,
            history=[ctx.callback.pack()]
        ).pack() if ctx.view_page > 0 else cbs.Dummy().pack(),
    )

    to_next_btn = Button(
        button_id='to_next_menu_page',
        text='▶️' if ctx.view_page < total_pages - 1 else '❌',
        callback_data=cbs.ChangePageTo(
            view_page=ctx.view_page + 1,
            history=[ctx.callback.pack()]
        ).pack() if ctx.view_page < total_pages - 1 else cbs.Dummy().pack(),
    )

    kb.insert(0, [to_first_btn, to_previous_btn, page_amount_btn, to_next_btn, to_last_btn])
    return kb


def default_finalizer_factory(back_button: bool = True):
    async def _default_finalizer(ui: UIRegistry, ctx: UIContext, menu: Menu) -> Menu:
        if not menu.footer_keyboard:
            menu.footer_keyboard = []

        total_pages = math.ceil(len(menu.keyboard) / ctx.max_elements_on_page) if menu.keyboard else 0
        navigation_buttons = await build_menu_navigation_buttons(
            ui,
            ctx,
            total_pages,
            back_button=back_button
        )
        menu.footer_keyboard.extend(navigation_buttons)

        if menu.keyboard:
            first_index = ctx.menu_page * ctx.max_elements_on_page
            last_index = first_index + ctx.max_elements_on_page
            menu.keyboard = menu.keyboard[first_index:last_index]

        return menu
    return _default_finalizer
