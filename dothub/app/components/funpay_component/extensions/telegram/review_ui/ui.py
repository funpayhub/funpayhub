from __future__ import annotations

from typing import Any
from html import escape

from hubplatform.i18n import i, im
from hubplatform.telegram.ui import (
    Button,
    MenuSpec,
    UIRegistry,
    MenuContext,
    MenuBuildContext,
    MenuBuildingSpec,
    KeyboardBlockSpec,
)
from funpaybotengine.types.pages import OrderPage
from hubplatform.app.components.telegram.ui.widgets import cancel_button, confirmable_button
from hubplatform.app.components.telegram.ui.finalizers import StripAndNavigationFinalizer

from ..menu_ids import MenuIDs as ExtensionMenuIDs
from .callbacks import Refund, AskRefund, ReplyInChat, ReplyInReview


class ReviewNotificationContext(MenuContext):
    order_page: OrderPage
    buyer_id: int
    buyer_username: str
    app_reply: str | None
    app_reply_errored: bool
    app_chat_reply: str | None
    app_chat_reply_errored: bool


class RefundMenuContext(MenuContext):
    order_id: str


registry = UIRegistry()


@registry.add_menu_builder(
    menu_id=ExtensionMenuIDs.review.review_notification_menu,
    context_type=ReviewNotificationContext,
)
class ReviewNotificationBuilder:
    async def __call__(
        self,
        ctx: MenuBuildContext[ReviewNotificationContext],
    ) -> MenuBuildingSpec:
        menu = MenuSpec()

        if not ctx.context.order_page.review or not ctx.context.order_page.review.rating:
            raise Exception

        rating = ctx.context.order_page.review.rating
        comment = ctx.context.order_page.review.text
        order_id = ctx.context.order_page.order_id
        order_name = str(ctx.context.order_page.short_description)
        chat_id = ctx.context.order_page.chat.id

        menu.header_text = (
            '<h3>'
            + i(
                key='app:funpay_component:telegram_extension:review_ui:notification_text',
                fallback=f'{"⭐️" * rating} за заказ '
                f' <b><a href="https://funpay.com/orders/{order_id}">'
                f'#{order_id} <h3><i>{escape(order_name)}</i></h3></a></b>',
                kwargs={
                    'stars': '⭐️' * rating,
                    'order': f'<b><a href="https://funpay.com/orders/{order_id}">'
                    f'#{order_id}</a></b>',
                },
            )
            + '</h3>'
        )

        comment = (
            f'<aside>{escape(comment or "")}'
            f'<cite><a href="https://funpay.com/users/{ctx.context.buyer_id}">'
            f'{ctx.context.buyer_username}</a></cite>'
            f'</aside>'
        )

        tables = []

        if ctx.context.app_reply_errored or ctx.context.app_reply is not None:
            content = (
                i('<b><u>❌ Произошла ошибка при ответе на отзыв.</u></b>')
                if ctx.context.app_reply_errored
                else escape(ctx.context.app_reply or '')
            )
            tables.append(
                t'<table bordered>'
                t'<tr><th align="left" valign="top">{i("⭐️ Ответ на отзыв")}</th></tr>'
                t'<tr><td align="left" valign="top">{content}</td></tr>'
                t'</table>',
            )

        if ctx.context.app_chat_reply_errored or ctx.context.app_chat_reply is not None:
            content = (
                i('<b><u>❌ Произошла ошибка при ответе в чате.</u></b>')
                if ctx.context.app_chat_reply_errored
                else escape(ctx.context.app_chat_reply or '')
            )
            tables.append(
                t'<table bordered>'
                t'<tr><th align="left" valign="top">{i("💬 Ответ в чате")}</th></tr>'
                t'<tr><td align="left" valign="top">{content}</td></tr>'
                t'</table>',
            )

        details_html = ''
        if tables:
            details_html = im(
                '<hr/>',
                '<details>',
                '<summary>',
                i('🤖 Авто-ответы'),
                '</summary>',
                *tables,
                '</details>',
            )

        menu.body_text = comment + details_html

        menu.main_keyboard.append(
            KeyboardBlockSpec.prerendered_block(
                block_id='app:funpay_component:telegram_extension:review_ui:first_block',
                block=[
                    Button(
                        button_id='reply',
                        text=i('💬 Ответить на отзыв'),
                        callback_data=ReplyInReview(order_id=order_id),
                    ),
                    Button(
                        button_id='reply',
                        text=i('💬 Написать в чат'),
                        callback_data=ReplyInChat(chat_id=chat_id),
                    ),
                ],
            ),
        )
        menu.main_keyboard.append(
            KeyboardBlockSpec.url_button(
                block_id='app:funpay_component:telegram_extension:review_ui:open_order',
                text='🌐 Открыть заказ',
                url=f'https://funpay.com/orders/{order_id}/',
            ),
        )

        menu.main_keyboard.append(
            KeyboardBlockSpec.callback_button(
                block_id='refund',
                text='💸 Вернуть средства',
                callback_data=AskRefund(order_id=order_id),
                style='danger',
            ),
        )
        return MenuBuildingSpec(menu=menu, finalizer=StripAndNavigationFinalizer())


@registry.add_menu_builder(
    menu_id=ExtensionMenuIDs.review.refund_menu,
    context_type=RefundMenuContext,
)
class RefundMenuBuilder:
    async def __call__(self, ctx: MenuBuildContext[RefundMenuContext]) -> MenuBuildingSpec:
        menu = MenuSpec()

        menu.header_text = f'<h3>‼️ Возврат средств по заказу #{ctx.context.order_id} ‼️</h3>'

        menu.main_keyboard.append(
            KeyboardBlockSpec.prerendered_block(
                block_id='app:funpay_component:review_ui:refund',
                block=confirmable_button(
                    id='refund',
                    ctx=ctx.context,
                    text='Вернуть',
                    style='danger',
                    cancel_buttons=5,
                    callback_data=Refund(order_id=ctx.context.order_id),
                ),
            ),
        )

        menu.footer_keyboard.append(
            KeyboardBlockSpec.prerendered_block(block_id='cancel', block=cancel_button()),
        )

        return MenuBuildingSpec(menu=menu, finalizer=StripAndNavigationFinalizer())


@registry.add_menu_builder(menu_id=ExtensionMenuIDs.review.enter_review_reply)
@registry.add_menu_builder(menu_id=ExtensionMenuIDs.review.enter_review_chat_reply)
async def build_menu(_: Any) -> MenuBuildingSpec:
    menu = MenuSpec()

    menu.header_text = '<h3>💬 Введите текст ответа.<h3>'
    menu.footer_keyboard.append(
        KeyboardBlockSpec.prerendered_block(
            block_id='cancel',
            block=cancel_button(),
        ),
    )
    return MenuBuildingSpec(menu=menu, finalizer=StripAndNavigationFinalizer())
