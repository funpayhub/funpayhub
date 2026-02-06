from __future__ import annotations

from . import modifications
from .ids import MenuIds
from .builders import (
    goods_ui,
    other_ui,
    control_ui,
    message_ui,
    formatters_ui,
    notifications_ui,
)


MENU_BUILDERS = [
    formatters_ui.FormatterListMenuBuilder,
    formatters_ui.FormatterInfoMenuBuilder,
    notifications_ui.NotificationsMenuBuilder,
    message_ui.NewMessageNotificationMenuBuilder,
    message_ui.SendMessageMenuBuilder,
    goods_ui.GoodsSourcesListMenuBuilder,
    goods_ui.GoodsSourceInfoMenuBuilder,
    goods_ui.AutoDeliveryGoodsSourcesListMenuBuilder,
    other_ui.MainMenuBuilder,
    other_ui.StartNotificationMenuBuilder,
    other_ui.FunPayStartNotificationMenuBuilder,
    other_ui.StateMenuBuilder,
    other_ui.AddAutoDeliveryRuleMenuBuilder,
    other_ui.RequestsMenuBuilder,
    control_ui.ControlMenuBuilder,
]


BUTTON_BUILDERS = []


MENU_MODIFICATIONS = {
    MenuIds.props_node: [
        modifications.PropertiesMenuModification,
        modifications.AutoDeliveryPropertiesMenuModification,
        modifications.AddOfferButtonModification,
        modifications.AddRemoveButtonToAutoDeliveryModification,
        modifications.ReplaceSourcesListButtonModification,
    ],
    MenuIds.props_param_manual_input: [
        modifications.AddFormattersListButtonModification,
    ],
    MenuIds.goods_source_info: [
        goods_ui.AddRemoveButtonToGoodsSourceInfoModification,
    ],
}
