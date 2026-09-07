from __future__ import annotations

import html
from typing import TYPE_CHECKING

from funpayhub.lib.translater import translater
from funpayhub.lib.telegram.ui import Menu, Button, MenuBuilder, MenuContext, KeyboardBuilder
from funpayhub.lib.base_app.telegram.app.ui.callbacks import OpenMenu
from funpayhub.lib.base_app.telegram.app.ui.ui_finalizers import (
    StripAndNavigationFinalizer,
    build_view_navigation_btns,
)

from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.telegram.ui.premade import AddRemoveButtonBaseModification

from . import callbacks as cbs


if TYPE_CHECKING:
    from funpayhub.lib.goods_sources import GoodsSource, GoodsSourcesManager


ru = translater.translate


class GoodsInfoMenuContext(MenuContext):
    source_id: str


class GoodsSourcesListMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.goods_sources_list,
    context_type=MenuContext,
):
    async def build(self, ctx: MenuContext, goods_manager: GoodsSourcesManager) -> Menu:
        kb = KeyboardBuilder()
        for source in goods_manager.values():
            kb.add_callback_button(
                button_id=f'open_source:{source.source_id}',
                text=f'[{len(source)}] {source.display_id}',
                callback_data=OpenMenu(
                    menu_id=MenuIds.goods_source_info,
                    context_data={'source_id': source.source_id},
                    ui_history=ctx.as_ui_history(),
                ).pack(),
            )

        footer_kb = KeyboardBuilder()
        footer_kb.add_callback_button(
            button_id='add_text_source',
            text=ru('➕ Добавить файл с товарами'),
            callback_data=cbs.AddGoodsTxtSource(ui_history=ctx.as_ui_history()).pack(),
        )

        return Menu(
            main_text=ru('🗳 Источники товаров'),
            main_keyboard=kb,
            footer_keyboard=footer_kb,
            finalizer=StripAndNavigationFinalizer(),
        )


class GoodsSourceInfoMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.goods_source_info,
    context_type=GoodsInfoMenuContext,
):
    async def build(self, ctx: GoodsInfoMenuContext, goods_manager: GoodsSourcesManager) -> Menu:
        source = goods_manager[ctx.source_id]
        kb = KeyboardBuilder()

        kb.add_row(
            Button.callback_button(
                button_id='download_goods',
                text=ru('⤵ Скачать товары'),
                callback_data=cbs.DownloadGoods(
                    source_id=source.source_id,
                    ui_history=ctx.as_ui_history(),
                ).pack(),
            ),
            Button.callback_button(
                button_id='upload_goods',
                text=ru('⤴ Выгрузить товары'),
                callback_data=cbs.UploadGoods(
                    source_id=source.source_id,
                    ui_history=ctx.as_ui_history(),
                ).pack(),
            ),
        )

        kb.add_row(
            Button.callback_button(
                button_id='add_goods',
                text=ru('➕ Добавить товары'),
                callback_data=cbs.AddGoods(
                    source_id=source.source_id,
                    ui_history=ctx.as_ui_history(),
                ).pack(),
            ),
            Button.callback_button(
                button_id='remove_goods',
                text=ru('🗑️ Удалить товары'),
                callback_data=cbs.RemoveGoods(
                    source_id=source.source_id,
                    ui_history=ctx.as_ui_history(),
                ).pack(),
            ),
        )

        kb.add_callback_button(
            button_id='reload_source',
            text=ru('🔄 Перезагрузить источник'),
            callback_data=cbs.ReloadGoodsSource(
                source_id=source.source_id,
                ui_history=ctx.as_ui_history(),
            ).pack(),
        )

        goods_text, min_index, max_index = await self._generate_text(source, ctx.view_page)
        text = ru(
            '🗳 Источник товаров <b><i>{goods_source_id}</i></b>.\n\n'
            '📊 Кол-во товаров: <b><i>{goods_amount}</i></b>.\n'
            '🧩 Тип источника: <b><i>{goods_source_type}</i></b>.\n'
            '🧭 Источник: <code class="language-Источник">{goods_source}</code>',
            goods_source_id=source.display_id,
            goods_amount=len(source),
            goods_source_type=ru(source.display_source_type),
            goods_source=ru(source.display_source),
        )
        text += '\n\n'
        text += (
            f'<pre>'
            f'<code class="language-{ru("Товары")} '
            f'{min_index + 1}-{max_index + 1}">'
            f'{goods_text}'
            f'</code></pre>\n'
        )

        return Menu(
            main_text=text,
            header_keyboard=await build_view_navigation_btns(ctx, -1),
            main_keyboard=kb,
            finalizer=StripAndNavigationFinalizer(),
        )

    async def _generate_text(self, source: GoodsSource, page: int = 0) -> tuple[str, int, int]:
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
                product = ru('❌ Товар слишком длинный.')

            line = f'{START + index + 1}. {product}\n'
            text += line

        return text, START, START + len(goods_batch) - 1


class AddRemoveButtonToGoodsSourceInfoModification(
    AddRemoveButtonBaseModification,
    modification_id='fph:add_remove_button_to_goods_source_info',
):
    async def modify(self, ctx: GoodsInfoMenuContext, menu: Menu) -> Menu:
        cb = cbs.RemoveGoodsSource(source_id=ctx.source_id, ui_history=ctx.ui_history).pack()
        return await self._modify(ctx, menu, 'delete_source', cb)
