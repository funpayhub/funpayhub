from __future__ import annotations


__all__ = ['build_navigation_buttons']

from aiogram.types import InlineKeyboardButton

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.lib.telegram.ui import Button, Keyboard, UIContext, UIRegistry
from funpayhub.lib.telegram.callbacks_parsing import join_callbacks


async def build_navigation_buttons(ui: UIRegistry, ctx: UIContext, total_pages: int) -> Keyboard:
    kb = []
    if ctx.callback.history:
        back_btn = InlineKeyboardButton(
            text=ui.translater.translate('$back', ctx.language),
            callback_data=join_callbacks(*ctx.callback.history),
        )
        kb = [[Button(id='back', obj=back_btn)]]

    if total_pages < 2:
        return kb

    page_amount_cb = (
        cbs.ChangePageManually(total_pages=total_pages).pack()
        if total_pages > 1
        else cbs.Dummy().pack()
    )
    page_amount_btn = InlineKeyboardButton(
        text=f'{ctx.menu_page + (1 if total_pages else 0)} / {total_pages}',
        callback_data=join_callbacks(ctx.callback.pack(), page_amount_cb),
    )

    to_first_cb = cbs.ChangePageTo(page=0).pack() if ctx.menu_page > 0 else cbs.Dummy().pack()
    to_first_btn = InlineKeyboardButton(
        text='⏪' if ctx.menu_page > 0 else '❌',
        callback_data=join_callbacks(ctx.callback.pack(), to_first_cb),
    )

    to_last_cb = (
        cbs.ChangePageTo(page=total_pages - 1).pack()
        if ctx.menu_page < total_pages - 1
        else cbs.Dummy().pack()
    )
    to_last_btn = InlineKeyboardButton(
        text='⏩' if ctx.menu_page < total_pages - 1 else '❌',
        callback_data=join_callbacks(ctx.callback.pack(), to_last_cb),
    )

    to_previous_cb = (
        cbs.ChangePageTo(page=ctx.menu_page - 1).pack()
        if ctx.menu_page > 0
        else cbs.Dummy().pack()
    )
    to_previous_btn = InlineKeyboardButton(
        text='◀️' if ctx.menu_page > 0 else '❌',
        callback_data=join_callbacks(ctx.callback.pack(), to_previous_cb),
    )

    to_next_cb = (
        cbs.ChangePageTo(page=ctx.menu_page + 1).pack()
        if ctx.menu_page < total_pages - 1
        else cbs.Dummy().pack()
    )
    to_next_btn = InlineKeyboardButton(
        text='▶️' if ctx.menu_page < total_pages - 1 else '❌',
        callback_data=join_callbacks(ctx.callback.pack(), to_next_cb),
    )

    kb.insert(
        0,
        [
            Button(id='to_first_page', obj=to_first_btn),
            Button(id='to_previous_page', obj=to_previous_btn),
            Button(id='page_counter', obj=page_amount_btn),
            Button(id='to_next_page', obj=to_next_btn),
            Button(id='to_last_page', obj=to_last_btn),
        ],
    )

    return kb
