from __future__ import annotations


__all__ = ['MenuIDs']


class AutoDeliveryMenuIDs:
    add_rule_menu = 'app:funpay_component:auto_delivery.add_rule'
    bind_source_list_menu = 'app:funpay_component:auto_delivery.bind_sources_list'


class AutoResponseMenuIDs:
    add_rule_menu = 'app:funpay_componant:auto_response.add_rule'


class ReviewMenuIDs:
    review_notification_menu = 'app:funpay_component:review_notification'


class MenuIDs:
    auto_delivery = AutoDeliveryMenuIDs
    auto_response = AutoResponseMenuIDs
    review = ReviewMenuIDs
