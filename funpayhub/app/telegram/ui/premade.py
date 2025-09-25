from __future__ import annotations


__all__ = ['build_menu_navigation_buttons']

from aiogram.types import InlineKeyboardButton

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.lib.telegram.ui import Button, Keyboard, UIContext, UIRegistry


async def build_menu_navigation_buttons(ui: UIRegistry, ctx: UIContext, total_pages: int) -> Keyboard:
    kb = []
    if ctx.callback.history:
        back_btn = InlineKeyboardButton(
            text=ui.translater.translate('$back', ctx.language),
            callback_data=ctx.callback.pack_history(),
        )
        kb = [[Button(id='back', obj=back_btn)]]

    if total_pages < 2:
        return kb

    page_amount_btn = InlineKeyboardButton(
        text=f'{ctx.menu_page + (1 if total_pages else 0)} / {total_pages}',
        callback_data=cbs.ChangeMenuPageManually(
            total_pages=total_pages,
            history=[ctx.callback.pack()]
        ).pack() if total_pages > 1 else cbs.Dummy().pack()
    )

    to_first_btn = InlineKeyboardButton(
        text='⏪' if ctx.menu_page > 0 else '❌',
        callback_data=cbs.ChangePageTo(
            menu_page=0,
            history=[ctx.callback.pack()]
        ).pack() if ctx.menu_page > 0 else cbs.Dummy().pack(),
    )

    to_last_btn = InlineKeyboardButton(
        text='⏩' if ctx.menu_page < total_pages - 1 else '❌',
        callback_data=cbs.ChangePageTo(
            menu_page=total_pages - 1,
            history=[ctx.callback.pack()]
        ).pack() if ctx.menu_page < total_pages - 1 else cbs.Dummy().pack(),
    )

    to_previous_btn = InlineKeyboardButton(
        text='◀️' if ctx.menu_page > 0 else '❌',
        callback_data=cbs.ChangePageTo(
            menu_page=ctx.menu_page - 1,
            history=[ctx.callback.pack()]
        ).pack() if ctx.menu_page > 0 else cbs.Dummy().pack(),
    )

    to_next_btn = InlineKeyboardButton(
        text='▶️' if ctx.menu_page < total_pages - 1 else '❌',
        callback_data=cbs.ChangePageTo(
            menu_page=ctx.menu_page + 1,
            history=[ctx.callback.pack()]
        ).pack() if ctx.menu_page < total_pages - 1 else cbs.Dummy().pack(),
    )

    kb.insert(
        0,
        [
            Button(id='to_first_menu_page', obj=to_first_btn),
            Button(id='to_previous_menu_page', obj=to_previous_btn),
            Button(id='menu_page_counter', obj=page_amount_btn),
            Button(id='to_next_menu_page', obj=to_next_btn),
            Button(id='to_last_menu_page', obj=to_last_btn),
        ],
    )

    return kb


async def build_view_navigation_buttons(ui: UIRegistry, ctx: UIContext, total_pages: int) -> Keyboard:
    kb = []

    if total_pages < 2:
        return kb

    page_amount_btn = InlineKeyboardButton(
        text=f'{ctx.view_page + (1 if total_pages else 0)} / {total_pages}',
        callback_data=cbs.ChangeViewPageManually(
            total_pages=total_pages,
            history=[ctx.callback.pack()]
        ).pack() if total_pages > 1 else cbs.Dummy().pack()
    )

    to_first_btn = InlineKeyboardButton(
        text='⏪' if ctx.view_page > 0 else '❌',
        callback_data=cbs.ChangePageTo(
            view_page=0,
            history=[ctx.callback.pack()]
        ).pack() if ctx.view_page > 0 else cbs.Dummy().pack(),
    )

    to_last_btn = InlineKeyboardButton(
        text='⏩' if ctx.view_page < total_pages - 1 else '❌',
        callback_data=cbs.ChangePageTo(
            view_page=total_pages - 1,
            history=[ctx.callback.pack()]
        ).pack() if ctx.view_page < total_pages - 1 else cbs.Dummy().pack(),
    )

    to_previous_btn = InlineKeyboardButton(
        text='◀️' if ctx.view_page > 0 else '❌',
        callback_data=cbs.ChangePageTo(
            view_page=ctx.view_page - 1,
            history=[ctx.callback.pack()]
        ).pack() if ctx.view_page > 0 else cbs.Dummy().pack(),
    )

    to_next_btn = InlineKeyboardButton(
        text='▶️' if ctx.view_page < total_pages - 1 else '❌',
        callback_data=cbs.ChangePageTo(
            view_page=ctx.view_page + 1,
            history=[ctx.callback.pack()]
        ).pack() if ctx.view_page < total_pages - 1 else cbs.Dummy().pack(),
    )

    kb.insert(
        0,
        [
            Button(id='to_first_view_page', obj=to_first_btn),
            Button(id='to_previous_view_page', obj=to_previous_btn),
            Button(id='view_page_counter', obj=page_amount_btn),
            Button(id='to_next_view_page', obj=to_next_btn),
            Button(id='to_last_view_page', obj=to_last_btn),
        ],
    )

    return kb