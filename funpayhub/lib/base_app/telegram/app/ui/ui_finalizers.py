from __future__ import annotations

import math
from typing import TYPE_CHECKING

from funpayhub.lib.telegram.ui import Button, KeyboardBuilder

from . import callbacks as cbs


if TYPE_CHECKING:
    from funpayhub.lib.translater import Translater as Tr
    from funpayhub.lib.telegram.ui import Menu, MenuContext
    from funpayhub.lib.base_app.telegram import TelegramApp


class StripAndNavigationFinalizer:
    def __init__(self, back_button: bool = True, max_lines_on_page: int | None = None) -> None:
        self.back_button = back_button
        self.max_lines_on_page = max_lines_on_page

    async def __call__(
        self, ctx: MenuContext, menu: Menu, tg: TelegramApp, translater: Tr
    ) -> Menu:
        max_lines = self.max_lines_on_page or tg.config.max_menu_lines
        total_pages = math.ceil(len(menu.main_keyboard) / max_lines) if menu.main_keyboard else 0

        navigation_buttons = build_menu_navigation_buttons(
            ctx=ctx,
            translater=translater,
            max_pages=total_pages,
            back_button=self.back_button,
        )
        menu.footer_keyboard.extend(navigation_buttons)

        if menu.main_keyboard:
            first_index = ctx.menu_page * max_lines
            last_index = first_index + max_lines

            menu.main_keyboard = menu.main_keyboard[first_index:last_index]
        return menu


def _btn(
    id: str,
    text: str,
    condition: bool,
    ctx: MenuContext,
    target_menu_page: int | None = None,
    target_view_page: int | None = None,
) -> Button:
    """Фабрика кнопок навигации по страницам."""
    return Button.callback_button(
        button_id=id,
        text=text if condition else ' ',
        callback_data=cbs.ChangePageTo(
            keyboard=target_menu_page,
            text=target_view_page,
            ui_history=ctx.as_ui_history(),
        ).pack()
        if condition and (target_menu_page is not None or target_view_page is not None)
        else cbs.Dummy().pack(),
    )


def build_menu_navigation_buttons(
    ctx: MenuContext,
    translater: Tr,
    max_pages: int,
    back_button: bool = True,
) -> KeyboardBuilder:
    kb = KeyboardBuilder()
    if ctx.ui_history and back_button:
        kb.add_callback_button(
            button_id='back',
            text=translater.translate('◀️ Назад'),
            callback_data=cbs.GoBack(ui_history=ctx.ui_history).pack(),
        )

    if max_pages < 2:
        return kb

    page_amount_btn = Button.callback_button(
        button_id='menu_page_counter',
        text=f'{ctx.menu_page + (1 if max_pages else 0)} / {max_pages}',
        callback_data=cbs.ActivateChangingPageState(
            mode='keyboard',
            total_pages=max_pages,
            ui_history=ctx.as_ui_history(),
        ).pack()
        if max_pages > 1
        else cbs.Dummy().pack(),
    )

    nav_kb = [
        _btn('first_kb_page', '⏪', ctx.menu_page > 0, ctx, 0),
        _btn('prev_kb_page', '◀️', ctx.menu_page > 0, ctx, ctx.menu_page - 1),
        page_amount_btn,
        _btn('next_kb_page', '▶️', ctx.menu_page < max_pages - 1, ctx, ctx.menu_page + 1),
        _btn('last_kb_page', '⏩', ctx.menu_page < max_pages - 1, ctx, max_pages - 1),
    ]
    kb.insert(0, nav_kb)
    return kb


async def build_view_navigation_buttons(
    ctx: MenuContext,
    total_pages: int = -1,
) -> KeyboardBuilder:
    kb: KeyboardBuilder = KeyboardBuilder()
    callback_data = ctx.callback_data

    unknown_max_pages = total_pages == -1

    if callback_data is None or (not unknown_max_pages and total_pages < 2):
        return kb

    page_amount_btn = Button.callback_button(
        button_id='menu_page_counter',
        text=f'{ctx.view_page + (1 if unknown_max_pages or total_pages else 0)}'
        + (f' / {total_pages}' if not unknown_max_pages else ''),
        callback_data=cbs.ActivateChangingPageState(
            mode='text',
            total_pages=total_pages,
            history=callback_data.as_history(),
        ).pack()
        if unknown_max_pages or total_pages > 1
        else cbs.Dummy().pack(),
    )

    nav_kb = [
        _btn('first_view_page', '⏪', ctx.view_page > 0, ctx, None, 0),
        _btn('previous_view_page', '◀️', ctx.view_page > 0, ctx, None, ctx.view_page - 1),
        page_amount_btn,
        _btn(
            'next_view_page',
            '▶️',
            unknown_max_pages or ctx.view_page < total_pages - 1,
            ctx,
            None,
            ctx.view_page + 1,
        ),
        _btn(
            'last_view_page',
            '⏩',
            not unknown_max_pages and ctx.view_page < total_pages - 1,
            ctx,
            None,
            total_pages - 1,
        ),
    ]

    kb.insert(0, nav_kb)
    return kb
