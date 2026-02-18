from __future__ import annotations

import html
from typing import TYPE_CHECKING
from dataclasses import dataclass

from funpayhub.lib.telegram.ui import Menu, Button, MenuBuilder, MenuContext, KeyboardBuilder
from funpayhub.lib.base_app.telegram.app.ui.callbacks import OpenMenu
from funpayhub.lib.base_app.telegram.app.ui.ui_finalizers import (
    StripAndNavigationFinalizer,
    build_view_navigation_buttons,
)

from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.telegram.ui.premade import AddRemoveButtonBaseModification

from . import callbacks as cbs


if TYPE_CHECKING:
    from funpayhub.lib.translater import Translater as Tr
    from funpayhub.lib.goods_sources import GoodsSource, GoodsSourcesManager


@dataclass(kw_only=True)
class GoodsInfoMenuContext(MenuContext):
    source_id: str


class GoodsSourcesListMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.goods_sources_list,
    context_type=MenuContext,
):
    async def build(
        self,
        ctx: MenuContext,
        goods_manager: GoodsSourcesManager,
        translater: Tr,
    ) -> Menu:
        kb = KeyboardBuilder()
        for source in goods_manager.values():
            kb.add_callback_button(
                button_id=f'open_source:{source.source_id}',
                text=f'[{len(source)}] {source.display_id}',
                callback_data=OpenMenu(
                    menu_id=MenuIds.goods_source_info,
                    context_data={'source_id': source.source_id},
                    from_callback=ctx.callback_data,
                ).pack(),
            )

        footer_kb = KeyboardBuilder()
        footer_kb.add_callback_button(
            button_id='add_text_source',
            text=translater.translate('➕ Добавить файл с товарами'),
            callback_data=cbs.AddGoodsTxtSource(from_callback=ctx.callback_data).pack(),
        )

        return Menu(
            main_text=translater.translate('🗳 Источники товаров'),
            main_keyboard=kb,
            footer_keyboard=footer_kb,
            finalizer=StripAndNavigationFinalizer(),
        )


class GoodsSourceInfoMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.goods_source_info,
    context_type=GoodsInfoMenuContext,
):
    async def build(
        self,
        ctx: GoodsInfoMenuContext,
        goods_manager: GoodsSourcesManager,
        translater: Tr,
    ) -> Menu:
        source = goods_manager[ctx.source_id]
        kb = KeyboardBuilder()

        kb.add_row(
            Button.callback_button(
                button_id='download_goods',
                text=translater.translate('⤵ Скачать товары'),
                callback_data=cbs.DownloadGoods(
                    source_id=source.source_id,
                    from_callback=ctx.callback_data,
                ).pack(),
            ),
            Button.callback_button(
                button_id='upload_goods',
                text=translater.translate('⤴ Выгрузить товары'),
                callback_data=cbs.UploadGoods(
                    source_id=source.source_id,
                    from_callback=ctx.callback_data,
                ).pack(),
            ),
        )

        kb.add_row(
            Button.callback_button(
                button_id='add_goods',
                text=translater.translate('➕ Добавить товары'),
                callback_data=cbs.AddGoods(
                    source_id=source.source_id,
                    from_callback=ctx.callback_data,
                ).pack(),
            ),
            Button.callback_button(
                button_id='remove_goods',
                text=translater.translate('🗑️ Удалить товары'),
                callback_data=cbs.RemoveGoods(
                    source_id=source.source_id,
                    from_callback=ctx.callback_data,
                ).pack(),
            ),
        )

        kb.add_callback_button(
            button_id='reload_source',
            text=translater.translate('🔄 Перезагрузить источник'),
            callback_data=cbs.ReloadGoodsSource(
                source_id=source.source_id,
                from_callback=ctx.callback_data,
            ).pack(),
        )

        goods_text, min_index, max_index = await self._generate_text(
            source,
            translater,
            ctx.view_page,
        )
        text = translater.translate(
            '🗳 Источник товаров <b><i>{goods_source_id}</i></b>.\n\n📊 Кол-во товаров: <b><i>{goods_amount}</i></b>.\n🧩 Тип источника: <b><i>{goods_source_type}</i></b>.\n🧭 Источник: <code class="language-Источник">{goods_source}</code>',
        ).format(
            goods_source_id=source.display_id,
            goods_amount=len(source),
            goods_source_type=translater.translate(source.display_source_type),
            goods_source=translater.translate(source.display_source),
        )
        text += '\n\n'
        text += (
            f'<pre>'
            f'<code class="language-{translater.translate("Товары")} '
            f'{min_index + 1}-{max_index + 1}">'
            f'{goods_text}'
            f'</code></pre>\n'
        )

        return Menu(
            main_text=text,
            header_keyboard=await build_view_navigation_buttons(ctx, -1),
            main_keyboard=kb,
            finalizer=StripAndNavigationFinalizer(),
        )

    async def _generate_text(
        self,
        source: GoodsSource,
        translater: Tr,
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
                product = translater.translate('❌ Товар слишком длинный.')

            line = f'{START + index + 1}. {product}\n'
            text += line

        return text, START, START + len(goods_batch) - 1


class AddRemoveButtonToGoodsSourceInfoModification(
    AddRemoveButtonBaseModification,
    modification_id='fph:add_remove_button_to_goods_source_info',
):
    async def modify(self, ctx: GoodsInfoMenuContext, menu: Menu, translater: Tr) -> Menu:
        delete_callback = cbs.RemoveGoodsSource(
            source_id=ctx.source_id,
            from_callback=ctx.callback_data,
        ).pack()
        return await self._modify(ctx, menu, translater, delete_callback=delete_callback)
