from __future__ import annotations

from typing import TYPE_CHECKING

import funpayhub.app.telegram.callbacks as cbs
from funpayhub.lib.translater import Translater
from funpayhub.app.telegram.ui import premade
from funpayhub.lib.telegram.ui.types import Menu, MenuBuilder, MenuContext, KeyboardBuilder
from funpayhub.lib.hub.text_formatters import FormattersRegistry
from funpayhub.app.utils.formatters_query_parser import parse_categories_query

from ..ids import MenuIds


if TYPE_CHECKING:
    pass


# Formatters
class FormatterListMenuBuilder(MenuBuilder):
    id = MenuIds.formatters_list
    context_type = MenuContext

    async def build(
        self,
        ctx: MenuContext,
        fp_formatters: FormattersRegistry,
        translater: Translater,
    ) -> Menu:
        keyboard = KeyboardBuilder()
        callback_data = ctx.callback_data

        if ctx.data.get('by_category'):
            for category in fp_formatters._categories_to_formatters.keys():
                keyboard.add_callback_button(
                    button_id=f'open_formatters_category:{category.id}',
                    text=translater.translate(category.name),
                    callback_data=cbs.OpenMenu(
                        menu_id=MenuIds.formatters_list,
                        data={'query': category.id},
                        history=callback_data.as_history() if callback_data is not None else [],
                    ).pack(),
                )
        else:
            if ctx.data.get('query'):
                query = parse_categories_query(ctx.data['query'])
                formatters = fp_formatters.get_formatters(query)
            else:
                formatters = fp_formatters._formatters.values()

            for formatter in formatters:
                keyboard.add_callback_button(
                    button_id=f'open_formatter_info:{formatter.key}',
                    text=translater.translate(formatter.name),
                    callback_data=cbs.OpenMenu(
                        menu_id=MenuIds.formatter_info,
                        data={'formatter_id': formatter.key},
                        history=callback_data.as_history() if callback_data is not None else [],
                    ).pack(),
                )

        footer_keyboard = KeyboardBuilder()
        if not ctx.data.get('query'):
            footer_keyboard.add_callback_button(
                button_id='open_formatters_by_category',
                text=translater.translate('$open_formatters_by_category'),
                callback_data=cbs.OpenMenu(
                    menu_id=MenuIds.formatters_list,
                    data={'by_category': not bool(ctx.data.get('by_category'))},
                    history=[callback_data.pack_history()] if callback_data is not None else [],
                ).pack(),
            )

        return Menu(
            text='Форматтеры',
            main_keyboard=keyboard,
            footer_keyboard=footer_keyboard,
            finalizer=premade.StripAndNavigationFinalizer(),
        )


class FormatterInfoMenuBuilder(MenuBuilder):
    id = MenuIds.formatter_info
    context_type = MenuContext

    async def build(
        self,
        ctx: MenuContext,
        fp_formatters: FormattersRegistry,
        translater: Translater,
    ) -> Menu:
        formatter = fp_formatters._formatters[ctx.data['formatter_id']]
        categories = fp_formatters._formatters_to_categories[formatter]
        categories_text = '; '.join(translater.translate(i.name) for i in categories)

        text = f"""{translater.translate(formatter.name)}

{translater.translate('$formatters:categories')}: <i>{categories_text}.</i>

{translater.translate(formatter.description)}
"""
        return Menu(
            text=text,
            finalizer=premade.StripAndNavigationFinalizer(),
        )
