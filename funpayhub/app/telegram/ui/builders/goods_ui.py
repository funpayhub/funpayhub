from __future__ import annotations

import html
from typing import TYPE_CHECKING

from funpayhub.app.telegram import callbacks as cbs
from funpayhub.lib.telegram.ui import Menu, Button, MenuBuilder, MenuContext, KeyboardBuilder
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.telegram.ui.premade import (
    StripAndNavigationFinalizer,
    build_view_navigation_buttons,
)
from funpayhub.app.telegram.ui.builders.context import GoodsInfoMenuContext


if TYPE_CHECKING:
    from funpayhub.lib.translater import Translater
    from funpayhub.lib.goods_sources import GoodsSource, GoodsSourcesManager


class GoodsSourcesListMenuBuilder(MenuBuilder):
    id = MenuIds.goods_sources_list
    context_type = MenuContext

    async def build(
        self,
        ctx: MenuContext,
        goods_manager: GoodsSourcesManager,
        translater: Translater,
    ) -> Menu:
        kb = KeyboardBuilder()
        for source in goods_manager.values():
            kb.add_callback_button(
                button_id=f'open_source:{source.source_id}',
                text=f'[{len(source)}] {source.display_id}',
                callback_data=cbs.OpenMenu(
                    menu_id=MenuIds.goods_source_info,
                    context_data={
                        'source_id': source.source_id,
                    },
                    history=ctx.callback_data.as_history() if ctx.callback_data else [],
                ).pack(),
            )

        return Menu(
            text=translater.translate('$goods_sources_list_text'),
            main_keyboard=kb,
            finalizer=StripAndNavigationFinalizer(),
        )


class GoodsSourceInfoMenuBuilder(MenuBuilder):
    id = MenuIds.goods_source_info
    context_type = GoodsInfoMenuContext

    async def build(
        self, ctx: GoodsInfoMenuContext, goods_manager: GoodsSourcesManager, translater: Translater
    ) -> Menu:
        source = goods_manager[ctx.source_id]
        kb = KeyboardBuilder()

        kb.add_row(
            Button.callback_button(
                button_id='download_goods',
                text=translater.translate('$download_goods'),
                callback_data=cbs.Dummy().pack(),
            ),
            Button.callback_button(
                button_id='upload_goods',
                text=translater.translate('$upload_goods'),
                callback_data=cbs.Dummy().pack(),
            ),
        )

        kb.add_row(
            Button.callback_button(
                button_id='add_goods',
                text=translater.translate('$add_goods'),
                callback_data=cbs.Dummy().pack(),
            ),
            Button.callback_button(
                button_id='remove_goods',
                text=translater.translate('$remove_goods'),
                callback_data=cbs.Dummy().pack(),
            ),
        )

        goods_text, min_index, max_index = await self._generate_text(
            source, translater, ctx.view_page
        )
        text = translater.translate('$goods_info_text').format(
            goods_source_id=source.display_id,
            goods_amount=len(source),
            goods_source_type=translater.translate(source.display_source_type),
            goods_source=translater.translate(source.display_source),
        )
        text += '\n\n'
        text += f'<pre><code class="language-{translater.translate("$goods_inline_text")} {min_index + 1}-{max_index + 1}">{goods_text}</code></pre>\n'

        return Menu(
            text=text,
            header_keyboard=await build_view_navigation_buttons(ctx, -1),
            main_keyboard=kb,
            finalizer=StripAndNavigationFinalizer(),
        )

    async def _generate_text(
        self,
        source: GoodsSource,
        translater: Translater,
        page: int = 0,
    ) -> tuple[str, int, int]:
        MAX_LINE_LEN = 120
        MAX_LINES = 30
        START = page * MAX_LINES

        goods_batch = await source.get_goods(MAX_LINES, START)

        if not goods_batch:
            return '', START, START

        text = ''
        for index, product in enumerate(goods_batch):
            product = html.escape(product).strip()
            if len(product) > MAX_LINE_LEN:
                product = translater.translate('$product_too_long')

            line = f'{START + index + 1}. {product}\n'
            text += line

        return text, START, START + len(goods_batch) - 1
