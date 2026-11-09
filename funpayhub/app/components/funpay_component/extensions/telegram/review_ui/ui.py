from __future__ import annotations

from html import escape

from hubplatform.i18n import I18nString, I18nMultiString
from hubplatform.telegram.ui import (
    MenuSpec,
    UIRegistry,
    MenuContext,
    MenuBuildContext,
    MenuBuildingSpec,
)
from hubplatform.app.components.telegram.ui.finalizers import StripAndNavigationFinalizer

from ..menu_ids import MenuIDs as ExtensionMenuIDs


class ReviewNotificationContext(MenuContext):
    order_id: str
    counterparty_id: str
    counterparty_username: str
    rating: int
    comment: str
    app_reply: str | None
    app_reply_errored: bool
    app_chat_reply: str | None
    app_chat_reply_errored: bool


registry = UIRegistry()


@registry.add_menu_builder(
    menu_id=ExtensionMenuIDs.review.review_notification_menu,
    context_type=ReviewNotificationContext,
)
async def review_notification_builder(
    ctx: MenuBuildContext[ReviewNotificationContext],
) -> MenuBuildingSpec:
    menu = MenuSpec()

    menu.header_text = I18nMultiString(
        '<p><b>',
        I18nString('Вы получили'),
        f' {"⭐️" * ctx.context.rating} ',
        I18nString('от'),
        f' <b><a href="https://funpay.com/users/{ctx.context.counterparty_id}">{ctx.context.counterparty_username}</a></b> ',
        I18nString('за заказ'),
        f' <b><a href="https://funpay.com/orders/{ctx.context.order_id}">#{ctx.context.order_id}</a></b>!',
        '</b></p>',
    )

    comment = I18nMultiString(f'<blockquote>{escape(ctx.context.comment)}</blockquote>')

    details = []
    if ctx.context.app_reply_errored:
        details.append(
            I18nMultiString(
                '<p><b>❌ Произошла ошибка при ответе на отзыв. Подробнее в логах.',
                '</b></p>',
            ),
        )

    if ctx.context.app_chat_reply_errored:
        details.append(
            I18nMultiString(
                '<p><b>❌ Произошла ошибка при ответе в чате. Подробнее в логах.',
                '</b></p>',
            ),
        )

    if ctx.context.app_reply is not None:
        details.append(
            I18nMultiString(
                '<p><b>',
                I18nString('Ответ на отзыв:'),
                '</b></p>',
                f'<blockquote>{escape(ctx.context.app_reply)}</blockquote>',
            ),
        )
    if ctx.context.app_chat_reply is not None:
        details.append(
            I18nMultiString(
                '<p><b>',
                I18nString('Ответ в чате:'),
                '</b></p>',
                f'<blockquote>{escape(ctx.context.app_chat_reply)}</blockquote>',
            ),
        )

    details_html = ''
    if details:
        details_html = I18nMultiString(
            '<hr/>',
            '<details>',
            '<summary>',
            I18nString('Авто-ответы'),
            '</summary>',
            *details,
            '</details>',
        )

    menu.body_text = comment + details_html
    return MenuBuildingSpec(menu=menu, finalizer=StripAndNavigationFinalizer())
