from __future__ import annotations

from .ids import MenuIds
from .builders import (
    goods_ui,
    other_ui,
    control_ui,
    message_ui,
    plugins_ui,
    formatters_ui,
    notifications_ui,
)
from . import modifications


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
    other_ui.AddCommandMenuBuilder,
    other_ui.StartNotificationMenuBuilder,
    other_ui.FunPayStartNotificationMenuBuilder,
    other_ui.UpdateMenuBuilder,
    other_ui.StateMenuBuilder,
    other_ui.InstallUpdateMenuBuilder,
    other_ui.AddAutoDeliveryRuleMenuBuilder,
    other_ui.RequestsMenuBuilder,
    control_ui.ControlMenuBuilder,
    plugins_ui.PluginsListMenuBuilder,
    plugins_ui.PluginInfoMenuBuilder,
    plugins_ui.InstallPluginMenuBuilder,
]


BUTTON_BUILDERS = []


MENU_MODIFICATIONS = {
    MenuIds.props_node: [
        modifications.PropertiesMenuModification,
        modifications.AddCommandButtonModification,
        modifications.AutoDeliveryPropertiesMenuModification,
        modifications.AddOfferButtonModification,
        modifications.AddRemoveButtonToAutoDeliveryModification,
        modifications.AddRemoveButtonToCommandModification,
        modifications.ReplaceSourcesListButtonModification,
    ],
    MenuIds.props_param_manual_input: [
        modifications.AddFormattersListButtonModification,
    ],
    MenuIds.goods_source_info: [
        goods_ui.AddRemoveButtonToGoodsSourceInfoModification,
    ],
}
