from __future__ import annotations

import html
import time
from typing import TYPE_CHECKING
from datetime import datetime
from collections.abc import Iterable

from pydantic import BaseModel
from hubplatform.telegram.ui import (
    Button,
    MenuSpec,
    UIRegistry,
    MenuContext,
    MenuBuildContext,
    MenuBuildingSpec,
    KeyboardBlockSpec,
)
from hubplatform.app.components.telegram.ui.finalizers import StripAndNavigationFinalizer
from hubplatform.app.components.telegram.properties.callbacks import NextValue

from dothub.loggers import funpay_component as logger
from dothub.app.components.funpay_component.offers_raiser import (
    RaisingCategory,
    get_raisable_categories,
)

from ..menu_ids import MenuIDs as ExtensionMenuIDs
from .callbacks import RerenderMenu, UpdateProfile


if TYPE_CHECKING:
    from funpaybotengine.types import Category

    from dothub.app.components.funpay_component import FunPayComponent, FunPayProperties


TIME_FORMAT = '%d.%m %H:%M'


def format_ts(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime(TIME_FORMAT)


def format_remaining(seconds: float) -> str:
    seconds = int(seconds)
    if seconds < 60:
        return f'{max(seconds, 0)} сек'

    parts = []
    for unit, size in (('д', 86400), ('ч', 3600), ('мин', 60)):
        amount, seconds = divmod(seconds, size)
        if amount:
            parts.append(f'{amount} {unit}')
    return ' '.join(parts)


def _next_raise_text(next_raise_at: float | None) -> str:
    if next_raise_at is None:
        return '🔄 поднимается...'
    remaining = format_remaining(next_raise_at - time.time())
    return f'⏳ {format_ts(next_raise_at)} (через {remaining})'


def _raise_status(state: RaisingCategory | None) -> str:
    if state is None:
        return '⏸ не поднимается'
    return _next_raise_text(state.next_raise_at)


def categories_table(rows: Iterable[tuple[str, str]]) -> str:
    """Renders ``(category name, next raise status)`` rows. Rows are sorted by name."""
    rendered = ''.join(
        f'<tr><td>{html.escape(name)}</td><td>{status}</td></tr>'
        for name, status in sorted(rows, key=lambda i: i[0].lower())
    )
    return (
        '<table bordered striped compact>'
        '<tr><td><b>Категория</b></td><td><b>Следующее поднятие</b></td></tr>'
        f'{rendered}'
        '</table>'
    )


class RaisedCategory(BaseModel):
    name: str
    next_raise_at: float | None


class OffersRaisedNotificationContext(MenuContext):
    categories: list[RaisedCategory]
    raised_at: float


registry = UIRegistry()


@registry.add_menu_builder(menu_id=ExtensionMenuIDs.offers_raiser.main)
async def offers_raiser_menu(
    ctx: MenuBuildContext[MenuContext],
    funpay_component: FunPayComponent,
    funpay_props: FunPayProperties,
) -> MenuBuildingSpec:
    menu = MenuSpec()
    menu.header_text = '<h2>🔺 Автоподнятие лотов</h2>'

    raiser = funpay_component.offers_raiser
    enabled = funpay_props.auto_raise.value

    body = f'<b>Статус: {"🟢 включено" if enabled else "🔴 выключено"}</b>'
    if enabled and not raiser.running:
        body += '<p><i>Поднятие начнётся после запуска FunPay компонента.</i></p>'
    body += '<hr/>'

    categories: dict[int, Category] = {
        category_id: state.category for category_id, state in raiser.categories.items()
    }
    profile_error = False
    if funpay_component.bot.userid != -1:
        try:
            profile = await funpay_component.profile()
            raisable = await get_raisable_categories(profile, funpay_component.bot)
            categories |= {
                category_id: category for category_id, (category, _) in raisable.items()
            }
        except Exception:
            logger.error('Unable to get profile categories for offers raiser menu.', exc_info=True)
            profile_error = True
    else:
        profile_error = True

    if categories:
        body += (
            f'<p>Категорий с лотами: <b>{len(categories)}</b>, '
            f'поднимается: <b>{len(raiser.categories)}</b>.</p>'
        ) + categories_table(
            (category.full_name, _raise_status(raiser.categories.get(category_id)))
            for category_id, category in categories.items()
        )
    elif profile_error:
        body += '<p>❌ Не удалось получить профиль FunPay.</p>'
    else:
        body += '<p>В профиле нет лотов, которые можно поднять.</p>'

    menu.body_text = body

    menu.main_keyboard.append(
        KeyboardBlockSpec.callback_button(
            block_id='app:funpay_component:offers_raiser:toggle',
            text='⏹ Выключить автоподнятие' if enabled else '▶️ Включить автоподнятие',
            callback_data=NextValue(node_path=list(funpay_props.auto_raise.path)),
            style='danger' if enabled else 'success',
        ),
    )
    menu.main_keyboard.append(
        KeyboardBlockSpec.prerendered_block(
            block_id='app:funpay_component:offers_raiser:update',
            block=[
                Button(
                    button_id='rerender',
                    text='🔄 Обновить',
                    callback_data=RerenderMenu(),
                ),
                Button(
                    button_id='update_profile',
                    text='👤 Обновить профиль',
                    callback_data=UpdateProfile(),
                ),
            ],
        ),
    )

    return MenuBuildingSpec(menu=menu, finalizer=StripAndNavigationFinalizer())

