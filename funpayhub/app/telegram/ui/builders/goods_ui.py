from __future__ import annotations

from typing import Any, TYPE_CHECKING

from funpayhub.app.telegram.ui.premade import StripAndNavigationFinalizer
from funpayhub.lib.telegram.ui import MenuBuilder, MenuContext, Menu, KeyboardBuilder
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.telegram import callbacks as cbs


if TYPE_CHECKING:
    from funpayhub.lib.goods_sources import GoodsSourcesManager
    from funpayhub.lib.translater import Translater


class GoodsSourcesListMenuBuilder(MenuBuilder):
    id = MenuIds.goods_sources_list
    context_type = MenuContext

    async def build(self, ctx: MenuContext, goods_manager: GoodsSourcesManager, translater: Translater) -> Menu:
        kb = KeyboardBuilder()
        for source in goods_manager.values():
            kb.add_callback_button(
                button_id=f'open_source:{source.source_id}',
                text=f'[{len(source)}] {source.display_id}',
                callback_data=cbs.Dummy().pack()
            )

        return Menu(
            text=translater.translate('$goods_sources_list_text'),
            main_keyboard=kb,
            finalizer=StripAndNavigationFinalizer()
        )
