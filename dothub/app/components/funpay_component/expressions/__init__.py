from __future__ import annotations


__all__ = [
    'FunPayOrderContext',
    'FunPayReviewContext',
    'FunPayMessageContext',
    'setup_funpay_component_expressions',
]

from hubplatform.expressions.manager import ExpressionsManager

from .context import FunPayOrderContext, FunPayReviewContext, FunPayMessageContext


def setup_funpay_component_expressions(manager: ExpressionsManager) -> None:
    """
    Registers context types, categories and expressions from FunPay component to
    passed expressions manager.
    """
    manager.add_context(FunPayOrderContext, 'funpay_component:order_context')
    manager.add_context(FunPayMessageContext, 'funpay_component:message_context')
    manager.add_context(FunPayReviewContext, 'funpay_component:review_context')
