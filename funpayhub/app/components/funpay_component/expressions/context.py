from __future__ import annotations


__all__ = [
    'FunPayOrderContext',
    'FunPayMessageContext',
    'FunPayReviewContext',
]


from hubplatform.i18n import I18nString
from funpaybotengine.types import Message, OrderPreview
from hubplatform.app.expressions.contexts import (
    GeneralOrderContext,
    GeneralReviewContext,
    GeneralMessageContext,
)


class FunPayOrderContext(
    GeneralOrderContext,
    name=I18nString(
        'app.funpay.expressions.contexts.order:name',
        'Заказы FunPay',
    ),
    description=I18nString(
        'app.funpay.expressions.contexts.order:description',
        'Выражения в этом контексте могут быть использованы, когда произошло событие, '
        'связанное с заказом на FunPay. Например: новый заказ, статус заказа изменился и т.д.',
    ),
):
    funpay_order_obj: OrderPreview


class FunPayMessageContext(
    GeneralMessageContext,
    name=I18nString(
        'app.funpay.expressions.contexts.message:name',
        'Сообщение на FunPay',
    ),
    description=I18nString(
        'app.funpay.expressions.contexts.message:description',
        'Выражения в этом контексте могут быть использованы, '
        'когда вы получили новое сообщение на FunPay.',
    ),
):
    funpay_message_obj: Message


class FunPayReviewContext(
    GeneralReviewContext,
    name=I18nString(
        'app.funpay.expressions.contexts.review:name',
        'Отзыв на FunPay',
    ),
    description=I18nString(
        'app.funpay.expressions.contexts.review:description',
        'Выражения в этом контексте могут быть использованы, когда произошло событие, '
        'связанное с отзывом на FunPay. Например: новый отзыв, отзыв был изменен и т.д.',
    ),
):
    pass
