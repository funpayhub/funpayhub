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
from .builders.properties_ui import builders as properties_ui
from .builders.properties_ui.registry import (
    PropertiesEntryMenuBuilder,
    PropertiesEntryButtonBuilder,
)


MENU_BUILDERS = [
    properties_ui.PropertiesMenuBuilder,
    properties_ui.ListParameterMenuBuilder,
    properties_ui.ChoiceParameterMenuBuilder,
    PropertiesEntryMenuBuilder,
    properties_ui.ParamValueManualInputMenuBuilder,
    properties_ui.AddListItemMenuBuilder,
    formatters_ui.FormatterListMenuBuilder,
    formatters_ui.FormatterInfoMenuBuilder,
    notifications_ui.NotificationsMenuBuilder,
    message_ui.NewMessageNotificationMenuBuilder,
    message_ui.SendMessageMenuBuilder,
    goods_ui.GoodsSourcesListMenuBuilder,
    goods_ui.GoodsSourceInfoMenuBuilder,
    other_ui.MainMenuBuilder,
    other_ui.AddCommandMenuBuilder,
    other_ui.StartNotificationMenuBuilder,
    other_ui.FunPayStartNotificationMenuBuilder,
    other_ui.UpdateMenuBuilder,
    other_ui.StateMenuBuilder,
    other_ui.InstallUpdateMenuBuilder,
    other_ui.AddAutoDeliveryRuleMenuBuilder,
    control_ui.ControlMenuBuilder,
    plugins_ui.PluginsListMenuBuilder,
    plugins_ui.PluginInfoMenuBuilder,
    plugins_ui.InstallPluginMenuBuilder,
]


BUTTON_BUILDERS = [
    properties_ui.ToggleParamButtonBuilder,
    properties_ui.ChangeParamValueButtonBuilder,
    properties_ui.OpenParamMenuButtonBuilder,
    PropertiesEntryButtonBuilder,
]


MENU_MODIFICATIONS = {
    MenuIds.properties_entry: [
        properties_ui.PropertiesMenuModification,
        properties_ui.AddCommandButtonModification,
        properties_ui.AutoDeliveryPropertiesMenuModification,
        properties_ui.AddOfferButtonModification,
    ],
    MenuIds.param_value_manual_input: [
        properties_ui.AddFormattersListButtonModification,
        properties_ui.AddSourcesListAtAutoDeliveryModification,
    ],
}
