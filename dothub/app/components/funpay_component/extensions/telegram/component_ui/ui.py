from __future__ import annotations

import html
from typing import TYPE_CHECKING

from hubplatform.telegram.ui import (
    MenuSpec,
    UIRegistry,
    MenuContext,
    MenuBuildContext,
    MenuBuildingSpec,
    KeyboardBlockSpec,
    MenuBuildingState,
)
from hubplatform.app.components.telegram.menu_ids import MenuIDs as PlatformMenuIDs
from hubplatform.app.components.telegram.ui.callbacks import OpenMenu
from hubplatform.app.components.telegram.ui.finalizers import StripAndNavigationFinalizer
from hubplatform.app.components.telegram.properties.builders import NodeMenuContext

from dothub.loggers import funpay_component as logger
from dothub.app.components.telegram_component.components.components_ui import (
    ComponentsUIMenuIDs,
)
lazy from dothub.app.components.funpay_component.component import FunPayComponentState

from ..menu_ids import MenuIDs as ExtensionMenuIDs
from .callbacks import UpdateProfile


if TYPE_CHECKING:
    from funpaybotengine import Bot
    from funpaybotengine.types.pages import ProfilePage
    from funpaybotengine.types.common import MoneyValue

    from dothub.app.components.funpay_component import FunPayComponent, FunPayProperties


def _format_money(money: MoneyValue | None) -> str:
    if money is None:
        return '—'
    return f'{money.value:,} {money.character}'.replace(',', ' ')


async def _count_categories(profile: ProfilePage, bot: Bot) -> tuple[int, int]:
    """Returns ``(categories amount, subcategories amount)`` of profile offers."""
    if not profile.offers:
        return 0, 0

    subcategories = {(type_, i) for type_, offers in profile.offers.items() for i in offers}
    subcategory_to_category = {
        (subcategory.type, subcategory.id): category.id
        for category in await bot.storage.get_categories()
        if category is not None
        for subcategory in category.subcategories
    }
    categories = {
        subcategory_to_category[i] for i in subcategories if i in subcategory_to_category
    }
    return len(categories), len(subcategories)


async def _profile_text(funpay_component: FunPayComponent) -> str:
    state = funpay_component.state
    if state is FunPayComponentState.NOT_AUTHENTICATED:
        return '<p>🔴 Не удалось войти в аккаунт: неверный golden key</p>'
    if state is FunPayComponentState.GOLDEN_KEY_CHECK_FAILED:
        return '<p>⚠️ Не удалось подключиться к FunPay</p>'

    try:
        profile = await funpay_component.profile()
        categories, subcategories = await _count_categories(profile, funpay_component.bot)
    except Exception:
        logger.error('Unable to get profile for FunPay component menu.', exc_info=True)
        return '<p>❌ Не удалось получить профиль FunPay</p>'

    header = profile.header
    user_id = header.user_id if header.user_id is not None else funpay_component.bot.userid
    username = html.escape(header.username or funpay_component.bot.username or str(user_id))
    profile_url = f'https://funpay.com/users/{user_id}/'
    sales = header.sales if header.sales is not None else '—'

    return (
        '<table bordered compact>'
        f'<tr><td>👤 Аккаунт</td><td><a href="{profile_url}">{username}</a></td></tr>'
        f'<tr><td>🪪 ID</td><td><a href="{profile_url}">{user_id}</a></td></tr>'
        f'<tr><td>💰 Баланс</td><td>{_format_money(header.balance)}</td></tr>'
        f'<tr><td>📦 Открытые продажи</td><td>{sales}</td></tr>'
        f'<tr><td>🗂 Категории</td><td>{categories}</td></tr>'
        f'<tr><td>🧩 Подкатегории</td><td>{subcategories}</td></tr>'
        '</table>'
    )


registry: UIRegistry = UIRegistry()


@registry.add_menu_builder(menu_id=ExtensionMenuIDs.component.main)
async def funpay_component_menu(
    ctx: MenuBuildContext[MenuContext],
    funpay_component: FunPayComponent,
    funpay_props: FunPayProperties,
) -> MenuBuildingSpec:
    menu = MenuSpec()
    menu.header_text = '<h2>🔷 FunPay</h2>'
    menu.body_text = await _profile_text(funpay_component)

    menu.main_keyboard.append(
        KeyboardBlockSpec.callback_button(
            block_id='app:funpay_component:component:settings',
            text='⚙️ Настройки компонента',
            callback_data=OpenMenu(
                menu_id=PlatformMenuIDs.properties.properties_menu,
                context=NodeMenuContext(node_path=list(funpay_props.path)).dump(),
            ),
        ),
    )
    menu.main_keyboard.append(
        KeyboardBlockSpec.callback_button(
            block_id='app:funpay_component:component:offers_raiser',
            text='🔺 Автоподнятие',
            callback_data=OpenMenu(
                menu_id=ExtensionMenuIDs.offers_raiser.main,
                context=MenuContext().dump(),
            ),
        ),
    )
    menu.main_keyboard.append(
        KeyboardBlockSpec.callback_button(
            block_id='app:funpay_component:component:first_response_cache',
            text='✉️ Кэш приветствий',
            callback_data=OpenMenu(
                menu_id=ExtensionMenuIDs.first_response_cache.chats_list,
                context=MenuContext().dump(),
            ),
        ),
    )

    if funpay_component.state is FunPayComponentState.RUNNING:
        menu.main_keyboard.append(
            KeyboardBlockSpec.callback_button(
                block_id='app:funpay_component:component:update_profile',
                text='👤 Обновить профиль',
                callback_data=UpdateProfile(),
            ),
        )

    return MenuBuildingSpec(menu=menu, finalizer=StripAndNavigationFinalizer())


@registry.add_menu_modification(
    menu_id=ComponentsUIMenuIDs.components_menu,
    modification_id='app:funpay_component:add_to_components_menu',
)
async def add_to_components_menu(
    ctx: MenuBuildContext[MenuContext],
    state: MenuBuildingState,
) -> MenuBuildingState:
    state.menu.main_keyboard.append(
        KeyboardBlockSpec.callback_button(
            block_id='app:funpay_component:open_component_menu',
            text='🔷 FunPay',
            callback_data=OpenMenu(
                menu_id=ExtensionMenuIDs.component.main,
                context=MenuContext().dump(),
            ),
        ),
    )
    return state
