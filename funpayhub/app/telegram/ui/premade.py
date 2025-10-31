from __future__ import annotations


__all__ = [
    'build_menu_navigation_buttons',
    'build_view_navigation_buttons',
    'StripAndNavigationFinalizer',
]

import math

from aiogram.types import InlineKeyboardButton

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.ui.types import Menu, Button, Keyboard, MenuContext
from funpayhub.lib.telegram.callback_data import UnknownCallback


class StripAndNavigationFinalizer:
    def __init__(
        self,
        back_button: bool = True,
        max_lines_on_page: int  | None = None,
        context_override: MenuContext | None = None,
    ) -> None:
        self.back_button = back_button
        self.max_lines_on_page = max_lines_on_page
        self.context_override = context_override

    async def __call__(
        self,
        ctx: MenuContext,
        menu: Menu,
        properties: FunPayHubProperties,
        translater: Translater
    ) -> Menu:
        ctx = self.context_override if self.context_override is not None else ctx
        if not menu.footer_keyboard:
            menu.footer_keyboard = []
        max_lines = self.max_lines_on_page or properties.telegram.appearance.menu_entries_amount.value
        total_pages = math.ceil(len(menu.main_keyboard) / max_lines) if menu.main_keyboard else 0

        navigation_buttons = await build_menu_navigation_buttons(
            ctx=ctx,
            translater=translater,
            total_pages=total_pages,
            back_button=self.back_button,
        )
        menu.footer_keyboard.extend(navigation_buttons)

        if menu.main_keyboard:
            first_index = ctx.menu_page * max_lines
            last_index = first_index + max_lines
            menu.main_keyboard = menu.main_keyboard[first_index:last_index]
        return menu


def _nav_button(
    id: str,
    text: str,
    condition: bool,
    callback_data: UnknownCallback,
    target_menu_page: int | None = None,
    target_view_page: int | None = None
) -> Button:
    """Фабрика кнопок навигации по страницам."""

    return Button(
        button_id=id,
        obj=InlineKeyboardButton(
            text=text if condition else ' ',
            callback_data=(
                cbs.ChangePageTo(
                    menu_page=target_menu_page,
                    view_page=target_view_page,
                    history=callback_data.as_history()
                ).pack()
                if condition and (target_menu_page is not None or target_view_page is not None)
                else cbs.Dummy().pack()
            ),
        ),
    )

async def build_menu_navigation_buttons(
    ctx: MenuContext,
    translater: Translater,
    total_pages: int,
    back_button: bool = True,
) -> Keyboard:
    if ctx.callback_data is None:
        return []

    kb: Keyboard = []
    callback_data = ctx.callback_data

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

    nav_kb = [
        _nav_button('first_menu_page', '⏪', ctx.menu_page > 0, callback_data, 0),
        _nav_button('previous_menu_page', '◀️', ctx.menu_page > 0, callback_data, ctx.menu_page - 1),
        page_amount_btn,
        _nav_button('next_menu_page', '▶️', ctx.menu_page < total_pages - 1, callback_data, ctx.menu_page + 1),
        _nav_button('last_menu_page', '⏩', ctx.menu_page < total_pages - 1, callback_data, total_pages - 1),
    ]
    kb.insert(0, nav_kb)
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

    nav_kb = [
        _nav_button('first_view_page', '⏪', ctx.view_page > 0, callback_data, None, 0),
        _nav_button('previous_view_page', '◀️', ctx.view_page > 0, callback_data, None, ctx.view_page - 1),
        page_amount_btn,
        _nav_button('next_view_page', '▶️', ctx.view_page < total_pages - 1, callback_data, None, ctx.view_page + 1),
        _nav_button('last_view_page', '⏩', ctx.view_page < total_pages - 1, callback_data, None, total_pages - 1),
    ]
    kb.insert(0, nav_kb)
    return kb
